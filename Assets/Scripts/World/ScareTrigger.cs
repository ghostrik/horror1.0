using System.Collections;
using UnityEngine;

/// <summary>
/// Одноразовый триггер-пугалка. Кладётся на объект с BoxCollider (IsTrigger).
/// Умеет: проиграть звук, захлопнуть дверь, погасить лампы, показать призрака, тряхнуть камеру, вывести фразу.
/// </summary>
public class ScareTrigger : MonoBehaviour
{
    [Header("Условия")]
    [Tooltip("Сработает только после стольких найденных предохранителей")]
    public int minFuses = 0;
    public float delay = 0f;

    [Header("Звук")]
    public AudioSource source;
    public AudioClip clip;
    [Range(0f, 1f)] public float volume = 1f;

    [Header("События")]
    public Door slamDoor;
    public FlickerLight[] killLights;
    public float killLightsDuration = 3f;
    public Apparition apparition;
    public float shake = 0f;
    public string message = "";

    bool fired;

    void Awake()
    {
        if (source != null) { source.spatialBlend = 1f; source.playOnAwake = false; source.rolloffMode = AudioRolloffMode.Linear; source.maxDistance = 25f; }
    }

    void OnTriggerEnter(Collider other)
    {
        if (fired) return;
        if (other.GetComponentInParent<PlayerController>() == null) return;
        var gm = GameManager.Instance;
        if (gm != null && (gm.FusesCollected < minFuses || !gm.IsPlaying)) return;
        fired = true;
        StartCoroutine(Fire());
    }

    IEnumerator Fire()
    {
        if (delay > 0f) yield return new WaitForSeconds(delay);
        if (source != null && clip != null) source.PlayOneShot(clip, volume);
        if (slamDoor != null) slamDoor.SlamShut();
        if (killLights != null)
            foreach (var l in killLights) if (l != null) l.ForceOff(killLightsDuration);
        if (apparition != null) apparition.Show();
        if (shake > 0f) PlayerController.AddShake(shake);
        if (!string.IsNullOrEmpty(message) && GameManager.Instance != null) GameManager.Instance.ShowMessage(message, 3f);
    }
}
