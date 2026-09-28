using UnityEngine;

/// <summary>
/// Фонарик: включение на F, батарея, мерцание на низком заряде и рядом с монстром,
/// инерционное покачивание за взглядом.
/// </summary>
public class Flashlight : MonoBehaviour
{
    public static Flashlight Instance { get; private set; }

    public Light spot;
    public Renderer lensRenderer;
    public AudioSource clickSource;
    public AudioClip clickClip;

    [Header("Батарея")]
    [Range(0f, 1f)] public float battery = 1f;
    public float secondsPerBattery = 260f;
    public bool isOn = true;

    [Header("Свет")]
    public float baseIntensity = 2.4f;
    public float baseRange = 20f;

    [Header("Покачивание")]
    public float swayAmount = 1.6f;
    public float swaySmooth = 7f;

    public bool IsLit => isOn && battery > 0f && spot != null && spot.enabled && spot.intensity > 0.3f;

    Quaternion baseLocalRot;
    Vector3 baseLocalPos;
    Vector2 sway;
    float flickerTimer;
    float flickerMul = 1f;
    MaterialPropertyBlock mpb;

    void Awake()
    {
        Instance = this;
        baseLocalRot = transform.localRotation;
        baseLocalPos = transform.localPosition;
        mpb = new MaterialPropertyBlock();
        if (clickSource != null) clickSource.spatialBlend = 0f;
    }

    public void AddBattery(float amount)
    {
        battery = Mathf.Clamp01(battery + amount);
    }

    void Update()
    {
        float dt = Time.deltaTime;
        bool playing = GameManager.Instance == null || GameManager.Instance.IsPlaying;

        if (playing && HInput.KeyDown(KeyCode.F))
        {
            isOn = !isOn;
            if (clickSource != null && clickClip != null) clickSource.PlayOneShot(clickClip, 0.7f);
        }

        if (isOn && battery > 0f) battery = Mathf.Max(0f, battery - dt / secondsPerBattery);

        // --- мерцание
        float fear = GameManager.Instance != null ? GameManager.Instance.MonsterProximity01 : 0f;
        float lowBattery = Mathf.InverseLerp(0.22f, 0.02f, battery);
        float instability = Mathf.Max(lowBattery, fear * 0.9f);
        flickerTimer -= dt;
        if (flickerTimer <= 0f)
        {
            if (Random.value < instability * 0.6f)
            {
                flickerMul = Random.Range(0f, 0.5f);
                flickerTimer = Random.Range(0.03f, 0.12f);
            }
            else
            {
                flickerMul = 1f;
                flickerTimer = Random.Range(0.05f, 0.4f);
            }
        }

        float batteryCurve = Mathf.Lerp(0.35f, 1f, Mathf.Clamp01(battery * 3f));
        float intensity = (isOn && battery > 0f) ? baseIntensity * batteryCurve * flickerMul : 0f;
        if (spot != null)
        {
            spot.enabled = intensity > 0.01f;
            spot.intensity = intensity;
            spot.range = baseRange * Mathf.Lerp(0.6f, 1f, batteryCurve);
        }
        if (lensRenderer != null)
        {
            lensRenderer.GetPropertyBlock(mpb);
            mpb.SetFloat("_Intensity", intensity > 0.01f ? 2.5f * (intensity / baseIntensity) : 0.02f);
            lensRenderer.SetPropertyBlock(mpb);
        }

        // --- инерция за взглядом
        Vector2 look = playing ? HInput.Look() : Vector2.zero;
        sway = Vector2.Lerp(sway, look * swayAmount, dt * swaySmooth);
        float speed = PlayerController.Instance != null ? PlayerController.Instance.CurrentSpeed : 0f;
        float walk = Mathf.Sin(Time.time * (speed > 2.5f ? 11f : 6.5f)) * Mathf.Clamp01(speed / 3f);
        transform.localRotation = baseLocalRot * Quaternion.Euler(sway.y * 2f + walk * 1.2f, -sway.x * 2f, -sway.x);
        transform.localPosition = baseLocalPos + new Vector3(-sway.x * 0.004f, -sway.y * 0.004f + walk * 0.006f, 0f);
    }
}
