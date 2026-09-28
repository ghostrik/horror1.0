using UnityEngine;

/// <summary>
/// "Режиссёр страха": время от времени устраивает мелкие события рядом с игроком —
/// далёкие удары, шёпот за спиной, скрежет, приступ мерцания, хлопок двери.
/// Чем дальше продвинулся игрок, тем чаще.
/// </summary>
public class AmbientDirector : MonoBehaviour
{
    public AudioSource oneShotSource;
    public AudioClip[] distantSounds;
    public AudioClip[] whisperSounds;
    public float minInterval = 22f;
    public float maxInterval = 55f;
    public float startDelay = 25f;

    float timer;
    Door[] doors;

    void Start()
    {
        timer = startDelay;
        doors = FindObjectsByType<Door>(FindObjectsSortMode.None);
        if (oneShotSource != null)
        {
            oneShotSource.spatialBlend = 1f;
            oneShotSource.rolloffMode = AudioRolloffMode.Linear;
            oneShotSource.minDistance = 2f;
            oneShotSource.maxDistance = 30f;
            oneShotSource.playOnAwake = false;
        }
    }

    void Update()
    {
        var gm = GameManager.Instance;
        if (gm == null || !gm.IsPlaying || PlayerController.Instance == null) return;

        float pace = 1f - Mathf.Clamp01(gm.FusesCollected / (float)Mathf.Max(1, gm.fusesRequired)) * 0.5f;
        timer -= Time.deltaTime;
        if (timer > 0f) return;
        timer = Random.Range(minInterval, maxInterval) * pace;

        float roll = Random.value;
        if (roll < 0.4f) PlayAround(distantSounds, 8f, 16f, false);
        else if (roll < 0.6f) PlayAround(whisperSounds, 1.5f, 3f, true);
        else if (roll < 0.85f) FlickerNearby();
        else SlamRandomDoor();
    }

    void PlayAround(AudioClip[] clips, float minDist, float maxDist, bool behind)
    {
        if (oneShotSource == null || clips == null || clips.Length == 0) return;
        Transform p = PlayerController.Instance.transform;
        Vector3 dir = behind ? -p.forward : Random.insideUnitSphere;
        dir.y = 0f;
        if (dir.sqrMagnitude < 0.01f) dir = -p.forward;
        dir = Quaternion.Euler(0f, Random.Range(-40f, 40f), 0f) * dir.normalized;
        oneShotSource.transform.position = p.position + dir * Random.Range(minDist, maxDist) + Vector3.up * 1.5f;
        oneShotSource.pitch = Random.Range(0.85f, 1.1f);
        oneShotSource.PlayOneShot(clips[Random.Range(0, clips.Length)], behind ? 0.55f : 0.9f);
    }

    void FlickerNearby()
    {
        Vector3 pp = PlayerController.Instance.transform.position;
        foreach (var l in FlickerLight.All)
        {
            if (l != null && Vector3.Distance(l.transform.position, pp) < 12f)
            {
                if (Random.value < 0.5f) l.ForceOff(Random.Range(0.8f, 2.5f));
                else l.Burst(Random.Range(1f, 3f));
            }
        }
    }

    void SlamRandomDoor()
    {
        if (doors == null || doors.Length == 0) return;
        Vector3 pp = PlayerController.Instance.transform.position;
        Door best = null;
        float bestScore = float.MaxValue;
        foreach (var d in doors)
        {
            if (d == null || !d.IsOpen || d.IsLocked) continue;
            float dist = Vector3.Distance(d.transform.position, pp);
            if (dist < 4f || dist > 18f) continue;
            float score = Mathf.Abs(dist - 9f) + Random.value * 4f;
            if (score < bestScore) { bestScore = score; best = d; }
        }
        if (best != null) best.SlamShut();
        else PlayAround(distantSounds, 8f, 14f, false);
    }
}
