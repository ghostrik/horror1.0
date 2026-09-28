using UnityEngine;

/// <summary>
/// Контроллер от первого лица: ходьба, бег с выносливостью, присед,
/// покачивание камеры, шаги, дыхание и тряска камеры.
/// </summary>
[RequireComponent(typeof(CharacterController))]
public class PlayerController : MonoBehaviour
{
    public static PlayerController Instance { get; private set; }

    [Header("Ссылки")]
    public Transform cameraRoot;
    public Transform cameraTransform;

    [Header("Движение")]
    public float walkSpeed = 2.3f;
    public float runSpeed = 4.6f;
    public float crouchSpeed = 1.2f;
    public float acceleration = 10f;
    public float gravity = -18f;

    [Header("Обзор")]
    public float mouseSensitivity = 2.0f;
    public float maxPitch = 82f;

    [Header("Рост")]
    public float standHeight = 1.8f;
    public float crouchHeight = 1.1f;
    public float standEye = 1.62f;
    public float crouchEye = 0.95f;

    [Header("Выносливость")]
    public float maxStamina = 6f;
    public float staminaRegen = 1.1f;
    public float staminaRegenDelay = 1.2f;

    [Header("Покачивание камеры")]
    public float bobFrequency = 1.9f;
    public float bobAmplitude = 0.045f;

    [Header("Звук")]
    public AudioSource footstepSource;
    public AudioSource breathSource;
    public AudioClip[] footstepClips;
    public float walkStride = 1.55f;
    public float runStride = 1.95f;

    public bool CanControl { get; set; } = true;
    public bool CanLook { get; set; } = true;
    public bool IsHidden { get; set; }
    public bool IsRunning { get; private set; }
    public bool IsCrouching { get; private set; }
    public float Stamina01 => stamina / maxStamina;
    public float CurrentSpeed { get; private set; }
    public Vector3 EyePosition => cameraTransform != null ? cameraTransform.position : transform.position + Vector3.up * standEye;

    CharacterController cc;
    Vector3 planarVelocity;
    float verticalVelocity;
    float yaw, pitch;
    float stamina;
    float regenTimer;
    bool exhausted;
    float bobPhase;
    float strideAccum;
    float eyeHeight;
    float trauma;
    Vector3 camBaseLocal;
    float landingDip;
    bool wasGrounded = true;

    void Awake()
    {
        Instance = this;
        cc = GetComponent<CharacterController>();
        stamina = maxStamina;
        eyeHeight = standEye;
        yaw = transform.eulerAngles.y;
        if (cameraTransform != null) camBaseLocal = cameraTransform.localPosition;
        mouseSensitivity = PlayerPrefs.GetFloat("hb_sensitivity", mouseSensitivity);
        if (footstepSource != null) { footstepSource.spatialBlend = 0f; footstepSource.playOnAwake = false; }
        if (breathSource != null) { breathSource.spatialBlend = 0f; breathSource.loop = true; breathSource.volume = 0f; if (!breathSource.isPlaying && breathSource.clip != null) breathSource.Play(); }
    }

    /// <summary>Добавить тряску камеры (0..1).</summary>
    public static void AddShake(float amount)
    {
        if (Instance != null) Instance.trauma = Mathf.Clamp01(Instance.trauma + amount);
    }

    public void SetLookRotation(Quaternion worldRotation)
    {
        Vector3 e = worldRotation.eulerAngles;
        yaw = e.y;
        pitch = Mathf.DeltaAngle(0f, e.x);
        ApplyLook();
    }

    void Update()
    {
        float dt = Time.deltaTime;
        bool playing = GameManager.Instance == null || GameManager.Instance.IsPlaying;
        bool control = CanControl && playing;

        if (CanLook && playing)
        {
            Vector2 look = HInput.Look() * mouseSensitivity;
            yaw += look.x;
            pitch = Mathf.Clamp(pitch - look.y, -maxPitch, maxPitch);
        }
        ApplyLook();

        if (!cc.enabled)
        {
            // в укрытии: тело не двигаем, только камера и дыхание
            CurrentSpeed = 0f;
            IsRunning = false;
            UpdateStamina(dt);
            UpdateCamera(dt);
            UpdateBreathing(dt);
            return;
        }

        // --- присед
        bool wantCrouch = control && (HInput.Key(KeyCode.LeftControl) || HInput.Key(KeyCode.C));
        if (!wantCrouch && IsCrouching)
        {
            // не встаём, если над головой что-то есть
            Vector3 top = transform.position + Vector3.up * (crouchHeight - cc.radius);
            if (Physics.SphereCast(top, cc.radius * 0.9f, Vector3.up, out _, standHeight - crouchHeight + 0.05f, ~0, QueryTriggerInteraction.Ignore))
                wantCrouch = true;
        }
        IsCrouching = wantCrouch;
        float targetHeight = IsCrouching ? crouchHeight : standHeight;
        cc.height = Mathf.MoveTowards(cc.height, targetHeight, dt * 4f);
        cc.center = new Vector3(0f, cc.height * 0.5f, 0f);
        eyeHeight = Mathf.Lerp(eyeHeight, IsCrouching ? crouchEye : standEye, dt * 8f);

        // --- движение
        Vector2 input = control ? HInput.Move() : Vector2.zero;
        bool wantRun = control && HInput.Key(KeyCode.LeftShift) && input.y > 0.1f && !IsCrouching && !exhausted;
        IsRunning = wantRun && input.sqrMagnitude > 0.01f;

        float speed = IsCrouching ? crouchSpeed : (IsRunning ? runSpeed : walkSpeed);
        Vector3 wish = (transform.right * input.x + transform.forward * input.y) * speed;
        planarVelocity = Vector3.MoveTowards(planarVelocity, wish, acceleration * dt);

        if (cc.isGrounded && verticalVelocity < 0f) verticalVelocity = -2f;
        verticalVelocity += gravity * dt;
        cc.Move((planarVelocity + Vector3.up * verticalVelocity) * dt);

        Vector3 flatVel = cc.velocity; flatVel.y = 0f;
        CurrentSpeed = flatVel.magnitude;

        if (!wasGrounded && cc.isGrounded) landingDip = 0.08f;
        wasGrounded = cc.isGrounded;

        UpdateStamina(dt);
        UpdateFootsteps(dt);
        UpdateCamera(dt);
        UpdateBreathing(dt);
    }

    void ApplyLook()
    {
        transform.rotation = Quaternion.Euler(0f, yaw, 0f);
        if (cameraRoot != null) cameraRoot.localRotation = Quaternion.Euler(pitch, 0f, 0f);
    }

    void UpdateStamina(float dt)
    {
        if (IsRunning && CurrentSpeed > 0.5f)
        {
            stamina -= dt;
            regenTimer = staminaRegenDelay;
            if (stamina <= 0f) { stamina = 0f; exhausted = true; }
        }
        else
        {
            regenTimer -= dt;
            if (regenTimer <= 0f) stamina = Mathf.Min(maxStamina, stamina + staminaRegen * dt * (IsCrouching ? 1.4f : 1f));
            if (exhausted && stamina > maxStamina * 0.35f) exhausted = false;
        }
    }

    void UpdateFootsteps(float dt)
    {
        if (!cc.isGrounded || CurrentSpeed < 0.3f) { strideAccum = Mathf.Min(strideAccum, 0.6f); return; }
        strideAccum += CurrentSpeed * dt;
        float stride = IsRunning ? runStride : walkStride;
        if (IsCrouching) stride *= 0.8f;
        if (strideAccum < stride) return;
        strideAccum = 0f;

        float noise = IsCrouching ? 1.2f : (IsRunning ? 13f : 5.5f);
        NoiseSystem.Emit(transform.position, noise);

        if (footstepSource != null && footstepClips != null && footstepClips.Length > 0)
        {
            var clip = footstepClips[Random.Range(0, footstepClips.Length)];
            footstepSource.pitch = Random.Range(0.88f, 1.08f) * (IsRunning ? 1.08f : 1f);
            float vol = IsCrouching ? 0.18f : (IsRunning ? 0.75f : 0.42f);
            footstepSource.PlayOneShot(clip, vol);
        }
    }

    void UpdateCamera(float dt)
    {
        if (cameraRoot != null)
        {
            Vector3 rp = cameraRoot.localPosition;
            rp.y = eyeHeight;
            cameraRoot.localPosition = rp;
        }
        if (cameraTransform == null) return;

        float fear = GameManager.Instance != null ? GameManager.Instance.Fear : 0f;
        float speed01 = Mathf.Clamp01(CurrentSpeed / runSpeed);
        bobPhase += dt * bobFrequency * Mathf.Lerp(0.6f, 1.7f, speed01) * Mathf.PI * (CurrentSpeed > 0.2f ? 1f : 0.25f);
        float amp = bobAmplitude * (CurrentSpeed > 0.2f ? Mathf.Lerp(0.6f, 1.6f, speed01) : 0.25f);
        if (IsCrouching) amp *= 0.6f;

        // дыхание в покое + страх добавляет дрожь
        float idleBreath = Mathf.Sin(Time.time * 1.3f) * 0.006f;
        Vector3 bob = new Vector3(Mathf.Cos(bobPhase) * amp * 0.6f, Mathf.Abs(Mathf.Sin(bobPhase)) * amp + idleBreath, 0f);

        landingDip = Mathf.MoveTowards(landingDip, 0f, dt * 0.4f);
        bob.y -= landingDip;

        trauma = Mathf.MoveTowards(trauma, 0f, dt * 0.8f);
        float shake = trauma * trauma + fear * 0.015f;
        float t = Time.time * 22f;
        Quaternion shakeRot = Quaternion.Euler(
            (Mathf.PerlinNoise(t, 0.1f) - 0.5f) * 10f * shake,
            (Mathf.PerlinNoise(0.3f, t) - 0.5f) * 10f * shake,
            (Mathf.PerlinNoise(t, t * 0.5f) - 0.5f) * 14f * shake + Mathf.Cos(bobPhase) * amp * 12f);

        cameraTransform.localPosition = camBaseLocal + bob;
        cameraTransform.localRotation = shakeRot;
    }

    void UpdateBreathing(float dt)
    {
        if (breathSource == null) return;
        float fear = GameManager.Instance != null ? GameManager.Instance.Fear : 0f;
        float exhaustion = 1f - Stamina01;
        float target = Mathf.Clamp01(exhaustion * 0.9f + fear * 0.5f) * 0.55f;
        breathSource.volume = Mathf.MoveTowards(breathSource.volume, target, dt * 0.5f);
        breathSource.pitch = Mathf.Lerp(0.9f, 1.25f, Mathf.Max(exhaustion, fear));
    }
}
