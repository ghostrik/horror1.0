using UnityEngine;

/// <summary>
/// Громкая связь ТЦ, которая живёт своей жизнью: гонг + искажённый голос + субтитры.
/// Звучит из всех динамиков сразу (несколько 3D-источников по залу).
/// </summary>
public class PASystem : MonoBehaviour
{
    public static PASystem Instance { get; private set; }

    public AudioSource[] speakers;
    public AudioClip chimeClip;
    public AudioClip[] voiceClips;
    public float minInterval = 70f;
    public float maxInterval = 140f;
    public float firstDelay = 55f;

    [TextArea(1, 3)]
    public string[] announcements =
    {
        "Уважаемые покупатели! Торговый центр «Галактика» работает для вас круглосуточно.",
        "Уважаемые покупатели... не покидайте... торговый зал... до окончания обслуживания.",
        "Внимание! Промоутер ждёт вас в отделе... в отделе... в отделе...",
        "Потерявшийся покупатель, подойдите к стойке информации. Вас ищут.",
        "Сегодня для вас особое предложение. Останьтесь. С нами. Навсегда.",
    };

    float timer;
    int index;

    void Awake()
    {
        Instance = this;
        timer = firstDelay;
        if (speakers != null)
            foreach (var s in speakers)
                if (s != null) { s.spatialBlend = 0.85f; s.playOnAwake = false; s.rolloffMode = AudioRolloffMode.Linear; s.minDistance = 4f; s.maxDistance = 45f; }
    }

    void Update()
    {
        var gm = GameManager.Instance;
        if (gm == null || !gm.IsPlaying) return;
        timer -= Time.deltaTime;
        if (timer > 0f) return;
        timer = Random.Range(minInterval, maxInterval);
        Announce(index++ % Mathf.Max(1, announcements.Length));
    }

    public void Announce(int i)
    {
        if (announcements == null || announcements.Length == 0) return;
        i = Mathf.Clamp(i, 0, announcements.Length - 1);
        if (speakers != null)
        {
            AudioClip voice = (voiceClips != null && voiceClips.Length > 0) ? voiceClips[i % voiceClips.Length] : null;
            foreach (var s in speakers)
            {
                if (s == null) continue;
                if (chimeClip != null) s.PlayOneShot(chimeClip, 0.8f);
                if (voice != null) s.PlayOneShot(voice, 0.9f);
            }
        }
        if (GameManager.Instance != null) GameManager.Instance.ShowSubtitle("<i>Громкая связь:</i> " + announcements[i], 6f);
    }
}
