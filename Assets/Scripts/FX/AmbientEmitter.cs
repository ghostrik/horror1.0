using UnityEngine;

/// <summary>
/// Зацикленный 3D-источник окружения (гул труб, капли, ветер в разбитом окне).
/// Стартует со случайного места клипа, чтобы источники не звучали в унисон.
/// </summary>
[RequireComponent(typeof(AudioSource))]
public class AmbientEmitter : MonoBehaviour
{
    public float minDistance = 1f;
    public float maxDistance = 14f;
    [Range(0f, 1f)] public float spatial = 1f;
    public float volumeWobble = 0.2f;

    AudioSource src;
    float baseVolume;
    float seed;

    void Awake()
    {
        src = GetComponent<AudioSource>();
        src.spatialBlend = spatial;
        src.loop = true;
        src.rolloffMode = AudioRolloffMode.Linear;
        src.minDistance = minDistance;
        src.maxDistance = maxDistance;
        src.dopplerLevel = 0f;
        baseVolume = src.volume;
        seed = Random.value * 50f;
        if (src.clip != null)
        {
            src.time = Random.Range(0f, src.clip.length * 0.95f);
            src.Play();
        }
    }

    void Update()
    {
        if (volumeWobble <= 0f) return;
        float n = Mathf.PerlinNoise(seed, Time.time * 0.15f);
        src.volume = baseVolume * (1f - volumeWobble + n * volumeWobble * 2f);
    }
}
