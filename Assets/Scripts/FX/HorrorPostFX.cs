using UnityEngine;

/// <summary>
/// Пост-обработка "камеры телефона" для Built-in RP: виньетка, зерно, хроматическая аберрация,
/// приглушённые цвета, дрожь картинки от страха, красная вспышка при скримере, строки развёртки.
/// </summary>
[RequireComponent(typeof(Camera))]
public class HorrorPostFX : MonoBehaviour
{
    public Shader shader;

    [Range(0f, 2f)] public float vignette = 0.55f;
    [Range(0f, 0.4f)] public float grain = 0.07f;
    [Range(0f, 0.01f)] public float chromatic = 0.0018f;
    [Range(0f, 1.5f)] public float saturation = 0.72f;
    [Range(0.5f, 2f)] public float contrast = 1.12f;
    [Range(0f, 0.5f)] public float scanlines = 0.06f;
    public Color tint = new Color(0.95f, 1f, 0.97f, 1f);

    [HideInInspector] public float fear;
    [HideInInspector] public float flash;

    Material mat;

    void OnEnable()
    {
        if (shader == null) shader = Shader.Find("Hidden/HorrorPostFX");
        if (shader != null && shader.isSupported) mat = new Material(shader) { hideFlags = HideFlags.HideAndDontSave };
    }

    void OnDisable()
    {
        if (mat != null) DestroyImmediate(mat);
    }

    void OnRenderImage(RenderTexture src, RenderTexture dst)
    {
        if (mat == null) { Graphics.Blit(src, dst); return; }
        mat.SetFloat("_Vignette", vignette);
        mat.SetFloat("_Grain", grain);
        mat.SetFloat("_Chroma", chromatic);
        mat.SetFloat("_Saturation", saturation);
        mat.SetFloat("_Contrast", contrast);
        mat.SetFloat("_Scan", scanlines);
        mat.SetFloat("_Fear", fear);
        mat.SetFloat("_Flash", flash);
        mat.SetColor("_Tint", tint);
        Graphics.Blit(src, dst, mat);
    }
}
