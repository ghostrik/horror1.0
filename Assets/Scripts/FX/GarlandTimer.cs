using UnityEngine;

/// <summary>
/// Гирлянда на таймере: сама включается, бежит огоньками, иногда гаснет.
/// Лампочки — дочерние рендеры с материалом Horror/UnlitGlow.
/// </summary>
public class GarlandTimer : MonoBehaviour
{
    public Renderer[] bulbs;
    public Light[] lights;
    public Color[] palette = { new Color(1f, 0.25f, 0.2f), new Color(1f, 0.8f, 0.25f), new Color(0.3f, 0.9f, 0.4f), new Color(0.3f, 0.5f, 1f) };
    public float chaseSpeed = 4f;
    public float onDuration = 40f;
    public float offDuration = 12f;
    public float startDelay = 6f;

    MaterialPropertyBlock mpb;
    float timer;
    bool on;
    float fade;
    float[] lightBase;

    void Awake()
    {
        mpb = new MaterialPropertyBlock();
        timer = startDelay;
        if (lights != null)
        {
            lightBase = new float[lights.Length];
            for (int i = 0; i < lights.Length; i++) if (lights[i] != null) lightBase[i] = lights[i].intensity;
        }
        Apply(0f);
    }

    void Update()
    {
        timer -= Time.deltaTime;
        if (timer <= 0f)
        {
            on = !on;
            timer = on ? onDuration * Random.Range(0.7f, 1.3f) : offDuration * Random.Range(0.6f, 1.4f);
        }
        fade = Mathf.MoveTowards(fade, on ? 1f : 0f, Time.deltaTime * (on ? 0.8f : 3f));
        Apply(fade);
    }

    void Apply(float f)
    {
        if (bulbs != null)
        {
            for (int i = 0; i < bulbs.Length; i++)
            {
                var b = bulbs[i];
                if (b == null) continue;
                float wave = 0.35f + 0.65f * Mathf.Clamp01(Mathf.Sin(Time.time * chaseSpeed - i * 0.9f) * 0.5f + 0.5f);
                Color c = palette.Length > 0 ? palette[i % palette.Length] : Color.white;
                b.GetPropertyBlock(mpb);
                mpb.SetColor("_Color", c);
                mpb.SetFloat("_Intensity", Mathf.Lerp(0.05f, 2.2f * wave, f));
                b.SetPropertyBlock(mpb);
            }
        }
        if (lights != null)
            for (int i = 0; i < lights.Length; i++)
                if (lights[i] != null) { lights[i].intensity = lightBase[i] * f; lights[i].enabled = f > 0.01f; }
    }
}
