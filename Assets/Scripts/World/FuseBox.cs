using UnityEngine;

/// <summary>
/// Электрощиток. Нужны все предохранители — тогда рубильник включает свет в зоне
/// (все объекты из powerOn), выключает аварийный свет (powerOff) и поднимает роллет.
/// </summary>
public class FuseBox : MonoBehaviour, IInteractable
{
    public GameObject[] fuseVisuals;
    public Transform lever;
    public GameObject[] powerOn;
    public GameObject[] powerOff;
    public RollingShutter shutter;
    public AudioSource source;
    public AudioClip insertClip;
    public AudioClip leverClip;
    public AudioClip powerUpClip;

    public bool Powered { get; private set; }
    int inserted;
    float leverAngle;

    public string Prompt
    {
        get
        {
            var gm = GameManager.Instance;
            int have = gm != null ? gm.FusesCollected : 0;
            if (inserted < RequiredFuses) return have > inserted ? "[E] Вставить предохранитель" : "[E] Осмотреть щиток";
            return "[E] Дёрнуть рубильник";
        }
    }

    public bool CanInteract => !Powered;
    int RequiredFuses => GameManager.Instance != null ? GameManager.Instance.fusesRequired : 3;

    void Awake()
    {
        if (source != null) { source.spatialBlend = 1f; source.playOnAwake = false; }
        if (fuseVisuals != null) foreach (var f in fuseVisuals) if (f != null) f.SetActive(false);
        SetPower(false);
    }

    public void Interact(PlayerController player)
    {
        var gm = GameManager.Instance;
        int have = gm != null ? gm.FusesCollected : 0;
        if (inserted < RequiredFuses)
        {
            if (have <= inserted)
            {
                gm?.ShowMessage($"Щиток обесточен. Не хватает предохранителей: {RequiredFuses - inserted}.");
                return;
            }
            while (inserted < have && inserted < RequiredFuses)
            {
                if (fuseVisuals != null && inserted < fuseVisuals.Length && fuseVisuals[inserted] != null) fuseVisuals[inserted].SetActive(true);
                inserted++;
            }
            if (source != null && insertClip != null) source.PlayOneShot(insertClip, 0.9f);
            NoiseSystem.Emit(transform.position, 5f);
            gm?.ShowMessage(inserted < RequiredFuses ? $"Вставил. Осталось: {RequiredFuses - inserted}." : "Все на месте. Теперь рубильник.");
            return;
        }

        Powered = true;
        if (source != null)
        {
            if (leverClip != null) source.PlayOneShot(leverClip, 1f);
            if (powerUpClip != null) source.PlayOneShot(powerUpClip, 1f);
        }
        NoiseSystem.Emit(transform.position, 30f); // монстр точно услышит
        SetPower(true);
        if (shutter != null) shutter.Open();
        gm?.OnPowerRestored();
    }

    void SetPower(bool on)
    {
        if (powerOn != null) foreach (var g in powerOn) if (g != null) g.SetActive(on);
        if (powerOff != null) foreach (var g in powerOff) if (g != null) g.SetActive(!on);
    }

    void Update()
    {
        if (lever == null) return;
        leverAngle = Mathf.MoveTowards(leverAngle, Powered ? -70f : 0f, Time.deltaTime * 400f);
        lever.localRotation = Quaternion.Euler(leverAngle, 0f, 0f);
    }
}
