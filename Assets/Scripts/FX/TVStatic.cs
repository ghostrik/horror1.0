using UnityEngine;

/// <summary>Телевизор с белым шумом: генерирует шумовую текстуру и дёргает свет экрана.</summary>
public class TVStatic : MonoBehaviour
{
    public Renderer screen;
    public Light screenLight;
    public AudioSource hiss;
    public int width = 96;
    public int height = 72;
    public float frameTime = 0.045f;

    Texture2D tex;
    Color32[] pixels;
    float timer;
    float baseIntensity;
    MaterialPropertyBlock mpb;
    int rollOffset;

    void Awake()
    {
        tex = new Texture2D(width, height, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Repeat };
        pixels = new Color32[width * height];
        mpb = new MaterialPropertyBlock();
        if (screenLight != null) baseIntensity = screenLight.intensity;
        if (hiss != null) { hiss.spatialBlend = 1f; hiss.loop = true; if (hiss.clip != null && !hiss.isPlaying) hiss.Play(); }
    }

    void Update()
    {
        timer -= Time.deltaTime;
        if (timer > 0f) return;
        timer = frameTime;

        rollOffset = (rollOffset + 2) % height;
        for (int y = 0; y < height; y++)
        {
            float band = ((y + rollOffset) % height) < 6 ? 0.55f : 1f;
            for (int x = 0; x < width; x++)
            {
                byte v = (byte)(Random.Range(20, 235) * band);
                pixels[y * width + x] = new Color32(v, v, (byte)Mathf.Min(255, v + 12), 255);
            }
        }
        tex.SetPixels32(pixels);
        tex.Apply(false);

        if (screen != null)
        {
            screen.GetPropertyBlock(mpb);
            mpb.SetTexture("_MainTex", tex);
            mpb.SetFloat("_Intensity", Random.Range(0.8f, 1.3f));
            screen.SetPropertyBlock(mpb);
        }
        if (screenLight != null) screenLight.intensity = baseIntensity * Random.Range(0.6f, 1.2f);
    }

    void OnDestroy()
    {
        if (tex != null) Destroy(tex);
    }
}
