using UnityEngine;

/// <summary>Лампа на проводе, раскачивающаяся от сквозняка.</summary>
public class SwingingLamp : MonoBehaviour
{
    public float amplitude = 9f;
    public float speed = 1.1f;
    public float secondaryAmplitude = 3f;
    public AudioSource creak;

    Quaternion baseRot;
    float seed;

    void Awake()
    {
        baseRot = transform.localRotation;
        seed = Random.value * 10f;
        if (creak != null) { creak.spatialBlend = 1f; creak.loop = true; if (creak.clip != null && !creak.isPlaying) creak.Play(); }
    }

    void Update()
    {
        float t = Time.time * speed + seed;
        float gust = 0.7f + Mathf.PerlinNoise(seed, Time.time * 0.2f) * 0.6f;
        float x = Mathf.Sin(t) * amplitude * gust;
        float z = Mathf.Sin(t * 0.73f + 1.3f) * secondaryAmplitude * gust;
        transform.localRotation = baseRot * Quaternion.Euler(x, 0f, z);
        if (creak != null) creak.pitch = 0.85f + Mathf.Abs(Mathf.Cos(t)) * 0.3f;
    }
}
