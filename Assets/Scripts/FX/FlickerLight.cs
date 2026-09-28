using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Лампа с характером: ровная, мерцающая, сломанная, свеча или аварийная пульсация.
/// Рядом с монстром любая лампа начинает сходить с ума.
/// </summary>
public class FlickerLight : MonoBehaviour
{
    public enum Mode { Steady, Flicker, Broken, Candle, Pulse }

    public static readonly List<FlickerLight> All = new List<FlickerLight>();

    public Light targetLight;
    public Renderer bulbRenderer;
    public AudioSource buzz;
    public Mode mode = Mode.Flicker;
    public float baseIntensity = 1f;
    [Range(0f, 1f)] public float chaos = 0.3f;
    public float pulseSpeed = 1.5f;
    public bool reactToMonster = true;

    float timer;
    float mul = 1f;
    float targetMul = 1f;
    float forcedOff;
    float seed;
    Vector3 basePos;
    MaterialPropertyBlock mpb;
    float buzzBase;

    void OnEnable() { All.Add(this); }
    void OnDisable() { All.Remove(this); }

    void Awake()
    {
        if (targetLight == null) targetLight = GetComponent<Light>();
        if (targetLight != null && baseIntensity <= 0f) baseIntensity = targetLight.intensity;
        seed = Random.value * 100f;
        basePos = transform.localPosition;
        mpb = new MaterialPropertyBlock();
        if (buzz != null)
        {
            buzz.spatialBlend = 1f;
            buzz.loop = true;
            buzz.rolloffMode = AudioRolloffMode.Linear;
            buzzBase = buzz.volume;
            if (buzz.clip != null) { buzz.time = Random.Range(0f, buzz.clip.length * 0.9f); buzz.Play(); }
        }
        if (mode == Mode.Broken) mul = targetMul = 0f;
    }

    /// <summary>Погасить на время (скриптовые события).</summary>
    public void ForceOff(float seconds)
    {
        forcedOff = Mathf.Max(forcedOff, seconds);
    }

    /// <summary>Устроить короткий приступ мерцания.</summary>
    public void Burst(float seconds)
    {
        timer = 0f;
        chaos = Mathf.Max(chaos, 0.95f);
        Invoke(nameof(ResetChaos), seconds);
    }

    float savedChaos = -1f;
    void ResetChaos() { if (savedChaos >= 0f) chaos = savedChaos; }
    void Start() { savedChaos = chaos; }

    void Update()
    {
        float dt = Time.deltaTime;
        timer -= dt;
        forcedOff -= dt;

        float monster = 0f;
        if (reactToMonster && MonsterAI.Instance != null && MonsterAI.Instance.IsActive)
        {
            float d = Vector3.Distance(MonsterAI.Instance.transform.position, transform.position);
            monster = Mathf.Clamp01(1f - (d - 2f) / 7f);
        }

        switch (mode)
        {
            case Mode.Steady:
                targetMul = 1f + (Mathf.PerlinNoise(seed, Time.time * 3f) - 0.5f) * 0.08f;
                break;
            case Mode.Flicker:
                if (timer <= 0f)
                {
                    bool off = Random.value < chaos * 0.5f;
                    targetMul = off ? Random.Range(0f, 0.25f) : Random.Range(0.85f, 1.05f);
                    timer = off ? Random.Range(0.02f, 0.12f) : Random.Range(0.08f, Mathf.Lerp(3f, 0.3f, chaos));
                }
                break;
            case Mode.Broken:
                if (timer <= 0f)
                {
                    bool sputter = Random.value < 0.35f + chaos * 0.3f;
                    targetMul = sputter ? Random.Range(0.3f, 1f) : 0f;
                    timer = sputter ? Random.Range(0.03f, 0.09f) : Random.Range(0.4f, 4f);
                }
                break;
            case Mode.Candle:
                targetMul = 0.8f + Mathf.PerlinNoise(seed, Time.time * 6f) * 0.35f;
                transform.localPosition = basePos + new Vector3(
                    (Mathf.PerlinNoise(seed, Time.time * 4f) - 0.5f) * 0.02f, 0f,
                    (Mathf.PerlinNoise(Time.time * 4f, seed) - 0.5f) * 0.02f);
                break;
            case Mode.Pulse:
                targetMul = Mathf.Pow(Mathf.Abs(Mathf.Sin(Time.time * pulseSpeed + seed)), 3f);
                break;
        }

        float m = targetMul;
        if (monster > 0f && Random.value < monster * 0.5f) m *= Random.Range(0f, 0.4f);
        if (forcedOff > 0f) m = 0f;

        mul = (mode == Mode.Candle || mode == Mode.Pulse || mode == Mode.Steady) ? Mathf.Lerp(mul, m, dt * 12f) : m;

        if (targetLight != null)
        {
            targetLight.intensity = baseIntensity * mul;
            targetLight.enabled = mul > 0.01f;
        }
        if (bulbRenderer != null)
        {
            bulbRenderer.GetPropertyBlock(mpb);
            mpb.SetFloat("_Intensity", Mathf.Lerp(0.03f, 1.6f, mul));
            bulbRenderer.SetPropertyBlock(mpb);
        }
        if (buzz != null)
        {
            buzz.volume = buzzBase * Mathf.Clamp01(mul + 0.15f) * (forcedOff > 0f ? 0f : 1f);
            buzz.pitch = 1f + (1f - mul) * 0.15f;
        }
    }
}
