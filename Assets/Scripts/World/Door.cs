using UnityEngine;

/// <summary>
/// Дверь на петле. Объект с этим скриптом — сама петля, створка — дочерний объект.
/// Открывается от игрока/монстра, скрипит, может быть заперта или требовать питание.
/// </summary>
public class Door : MonoBehaviour, IInteractable
{
    [Header("Поведение")]
    public float openAngle = 100f;
    public float openSpeed = 2.2f;
    public float slamSpeed = 7f;
    public bool startOpen = false;
    public bool locked = false;
    public bool requiresPower = false;
    [Tooltip("Входная решётка ТЦ: при попытке открыть обновляет цель")]
    public bool isEntranceGrate = false;
    [TextArea] public string lockedMessage = "Заперто.";

    [Header("Звук")]
    public AudioSource audioSource;
    public AudioClip openClip;
    public AudioClip closeClip;
    public AudioClip lockedClip;
    public AudioClip slamClip;
    public AudioClip unlockClip;

    public bool IsOpen { get; private set; }
    public bool IsLocked => locked || (requiresPower && (GameManager.Instance == null || !GameManager.Instance.PowerRestored));

    Quaternion closedRot;
    float angle;
    float targetAngle;
    float currentSpeed;
    float lockedCooldown;

    public string Prompt
    {
        get
        {
            if (IsLocked) return "[E] Дёрнуть ручку";
            return IsOpen ? "[E] Закрыть" : "[E] Открыть";
        }
    }

    public bool CanInteract => true;

    void Awake()
    {
        closedRot = transform.localRotation;
        if (audioSource != null) { audioSource.spatialBlend = 1f; audioSource.playOnAwake = false; }
        if (startOpen)
        {
            IsOpen = true;
            angle = targetAngle = openAngle * 0.85f;
            transform.localRotation = closedRot * Quaternion.Euler(0f, angle, 0f);
        }
        currentSpeed = openSpeed;
    }

    public void Interact(PlayerController player)
    {
        if (IsLocked)
        {
            if (lockedCooldown > 0f) return;
            lockedCooldown = 0.8f;
            Play(lockedClip, 0.8f);
            NoiseSystem.Emit(transform.position, 6f);
            if (GameManager.Instance != null && isEntranceGrate) GameManager.Instance.OnGrateJammed();
            if (GameManager.Instance != null)
                GameManager.Instance.ShowMessage(requiresPower ? "Электрозамок. Без питания не откроется." : lockedMessage);
            return;
        }
        if (IsOpen) Close(false);
        else Open(player != null ? player.transform.position : transform.position - transform.forward, false);
    }

    /// <summary>Открыть в сторону от точки from.</summary>
    public void Open(Vector3 from, bool slam)
    {
        if (IsOpen && !slam) return;
        // Створка смотрит вдоль +X локально, нормаль двери — локальная ось Z.
        Vector3 local = transform.InverseTransformPoint(from);
        float sign = local.z > 0f ? 1f : -1f;
        targetAngle = openAngle * sign;
        IsOpen = true;
        currentSpeed = slam ? slamSpeed : openSpeed;
        Play(slam ? slamClip : openClip, slam ? 1f : 0.75f);
        NoiseSystem.Emit(transform.position, slam ? 14f : 7f);
        if (slam) PlayerController.AddShake(ShakeByDistance(0.35f));
    }

    public void Close(bool slam)
    {
        if (!IsOpen) return;
        IsOpen = false;
        targetAngle = 0f;
        currentSpeed = slam ? slamSpeed * 1.4f : openSpeed;
        if (!slam) Play(closeClip, 0.6f);
        NoiseSystem.Emit(transform.position, slam ? 14f : 6f);
    }

    public void Unlock()
    {
        locked = false;
        requiresPower = false;
        Play(unlockClip, 1f);
    }

    float slamPending = -1f;

    void Update()
    {
        lockedCooldown -= Time.deltaTime;
        angle = Mathf.MoveTowards(angle, targetAngle, currentSpeed * Time.deltaTime * Mathf.Max(20f, Mathf.Abs(targetAngle - angle) * 2.2f));
        transform.localRotation = closedRot * Quaternion.Euler(0f, angle, 0f);

        // звук удара при захлопывании — когда створка дошла до косяка
        if (slamPending > 0f && Mathf.Abs(angle) < 1f)
        {
            Play(slamClip, 1f);
            PlayerController.AddShake(ShakeByDistance(0.45f));
            slamPending = -1f;
        }
    }

    /// <summary>Резко захлопнуть (скриптовое событие).</summary>
    public void SlamShut()
    {
        if (!IsOpen) return;
        Close(true);
        slamPending = 1f;
    }

    float ShakeByDistance(float max)
    {
        if (PlayerController.Instance == null) return 0f;
        float d = Vector3.Distance(PlayerController.Instance.transform.position, transform.position);
        return max * Mathf.Clamp01(1f - d / 12f);
    }

    void Play(AudioClip clip, float vol)
    {
        if (audioSource != null && clip != null)
        {
            audioSource.pitch = Random.Range(0.92f, 1.06f);
            audioSource.PlayOneShot(clip, vol);
        }
    }
}
