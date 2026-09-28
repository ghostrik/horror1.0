using UnityEngine;

/// <summary>
/// Силуэт, который появляется на мгновение и исчезает, когда на него посмотрели
/// или подошли слишком близко. Изначально объект выключен визуально.
/// </summary>
public class Apparition : MonoBehaviour
{
    public GameObject visual;
    public float maxLifetime = 4f;
    public float vanishWhenLookedFor = 0.35f;
    public float vanishDistance = 4f;
    public AudioSource source;
    public AudioClip vanishClip;
    public Light glow;

    float life;
    float lookTime;
    bool shown;

    void Awake()
    {
        if (visual != null) visual.SetActive(false);
        if (glow != null) glow.enabled = false;
        if (source != null) { source.spatialBlend = 1f; source.playOnAwake = false; }
    }

    public void Show()
    {
        shown = true;
        life = 0f;
        lookTime = 0f;
        if (visual != null) visual.SetActive(true);
        if (glow != null) glow.enabled = true;
    }

    void Update()
    {
        if (!shown) return;
        life += Time.deltaTime;

        var p = PlayerController.Instance;
        if (p != null)
        {
            Vector3 toMe = transform.position + Vector3.up * 1.6f - p.EyePosition;
            float dist = toMe.magnitude;
            Transform cam = p.cameraTransform != null ? p.cameraTransform : p.transform;
            if (Vector3.Angle(cam.forward, toMe) < 18f) lookTime += Time.deltaTime;
            if (dist < vanishDistance) lookTime = vanishWhenLookedFor;
        }

        // дрожит и чуть "плывёт"
        if (visual != null)
            visual.transform.localPosition = new Vector3(Mathf.Sin(Time.time * 40f) * 0.01f, 0f, 0f);

        if (lookTime >= vanishWhenLookedFor || life > maxLifetime) Vanish();
    }

    void Vanish()
    {
        shown = false;
        if (visual != null) visual.SetActive(false);
        if (glow != null) glow.enabled = false;
        if (source != null && vanishClip != null) source.PlayOneShot(vanishClip, 0.8f);
        PlayerController.AddShake(0.25f);
    }
}
