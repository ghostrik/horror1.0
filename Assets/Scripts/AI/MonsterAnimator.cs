using UnityEngine;

/// <summary>
/// Процедурная анимация Мерчандайзера без Animator-а: механическая походка манекена,
/// "лаги" (поза замирает и рывком перескакивает), резкие повороты головы,
/// руки тянутся вперёд в погоне, отваливающаяся челюсть-маска, скример.
/// Глаза — светодиодные табло с бегущей строкой.
/// Все кости — обычные пустышки-пивоты в иерархии монстра.
/// </summary>
public class MonsterAnimator : MonoBehaviour
{
    [Header("Пивоты")]
    public Transform body;
    public Transform torso;
    public Transform head;
    public Transform jaw;
    public Transform armL;
    public Transform armR;
    public Transform foreArmL;
    public Transform foreArmR;
    public Transform legL;
    public Transform legR;
    public Transform kneeL;
    public Transform kneeR;

    [Header("Параметры")]
    public float strideFrequency = 1.25f;
    public float legSwing = 32f;
    public float armSwing = 24f;

    [Header("Светодиодные глаза")]
    public Renderer[] ledRenderers;
    public float ledScrollSpeed = 0.35f;
    [Tooltip("Сколько строк в текстуре табло")]
    public int ledRows = 4;

    [HideInInspector] public float speed;
    [HideInInspector] public bool frozen;
    [HideInInspector] public int ledMode;
    [HideInInspector] public bool chasing;
    [HideInInspector] public bool jumpscare;

    Quaternion bodyR, torsoR, headR, jawR, armLR, armRR, faLR, faRR, legLR, legRR, knLR, knRR;
    Vector3 bodyP;
    float phase;
    float twitchTimer;
    Quaternion twitchTarget = Quaternion.identity;
    Quaternion twitchCurrent = Quaternion.identity;
    float lunge;
    float reach;
    float ledScroll;
    float ledGlitch;
    MaterialPropertyBlock mpb;

    void Awake()
    {
        bodyR = R(body); torsoR = R(torso); headR = R(head); jawR = R(jaw);
        armLR = R(armL); armRR = R(armR); faLR = R(foreArmL); faRR = R(foreArmR);
        legLR = R(legL); legRR = R(legR); knLR = R(kneeL); knRR = R(kneeR);
        if (body != null) bodyP = body.localPosition;
        mpb = new MaterialPropertyBlock();
    }

    static Quaternion R(Transform t) => t != null ? t.localRotation : Quaternion.identity;

    public void Lunge() { lunge = 1f; }

    /// <summary>Рывок после "лага": голова и табло дёргаются.</summary>
    public void Glitch()
    {
        twitchTimer = 0f;
        ledGlitch = 0.25f;
    }

    void Update()
    {
        float dt = Time.deltaTime;
        UpdateLeds(dt);
        if (frozen && !jumpscare) return; // поза застыла — как зависшая аниматроника
        float move01 = Mathf.Clamp01(speed / 3.5f);
        phase += dt * strideFrequency * Mathf.Max(0.2f, speed) * Mathf.PI;
        lunge = Mathf.MoveTowards(lunge, 0f, dt * 2.5f);
        reach = Mathf.MoveTowards(reach, (chasing || jumpscare) ? 1f : 0f, dt * 2f);

        float s = Mathf.Sin(phase);
        float c = Mathf.Cos(phase);
        float limp = Mathf.Max(0f, Mathf.Sin(phase * 0.5f)) * 0.3f; // приволакивает ногу

        // --- ноги
        Set(legL, legLR, Quaternion.Euler(s * legSwing * move01, 0f, 0f));
        Set(legR, legRR, Quaternion.Euler(-s * legSwing * move01 * (1f - limp), 0f, 0f));
        Set(kneeL, knLR, Quaternion.Euler(Mathf.Max(0f, -c) * 40f * move01, 0f, 0f));
        Set(kneeR, knRR, Quaternion.Euler(Mathf.Max(0f, c) * 40f * move01, 0f, 0f));

        // --- тело: наклон вперёд в погоне, покачивание
        float breathe = Mathf.Sin(Time.time * 1.1f);
        if (body != null)
            body.localPosition = bodyP + new Vector3(0f, Mathf.Abs(s) * 0.06f * move01 - limp * 0.05f + breathe * 0.01f, 0f);
        Set(body, bodyR, Quaternion.Euler(0f, 0f, s * 4f * move01 + limp * 6f));
        Set(torso, torsoR, Quaternion.Euler(Mathf.Lerp(6f, 24f, reach) + lunge * 18f + breathe * 1.5f, s * 6f * move01, 0f));

        // --- руки: болтаются или тянутся вперёд
        float armJitter = (Mathf.PerlinNoise(Time.time * 6f, 1f) - 0.5f) * 10f;
        Quaternion swingL = Quaternion.Euler(-s * armSwing * move01 + armJitter, 0f, 6f);
        Quaternion swingR = Quaternion.Euler(s * armSwing * move01 - armJitter, 0f, -6f);
        Quaternion reachL = Quaternion.Euler(-78f + s * 8f, 8f, 10f);
        Quaternion reachR = Quaternion.Euler(-72f - s * 8f, -8f, -10f);
        Set(armL, armLR, Quaternion.Slerp(swingL, reachL, reach));
        Set(armR, armRR, Quaternion.Slerp(swingR, reachR, reach));
        Set(foreArmL, faLR, Quaternion.Euler(Mathf.Lerp(-10f, -25f, reach) + Mathf.Sin(Time.time * 13f) * 4f * reach, 0f, 0f));
        Set(foreArmR, faRR, Quaternion.Euler(Mathf.Lerp(-12f, -20f, reach) + Mathf.Cos(Time.time * 11f) * 4f * reach, 0f, 0f));

        // --- голова: резкие рывки
        twitchTimer -= dt;
        if (twitchTimer <= 0f)
        {
            twitchTimer = jumpscare ? 0.05f : Random.Range(chasing ? 0.15f : 0.5f, chasing ? 0.8f : 2.8f);
            float amp = jumpscare ? 1.6f : 1f;
            twitchTarget = Quaternion.Euler(Random.Range(-15f, 20f) * amp, Random.Range(-30f, 30f) * amp, Random.Range(-40f, 40f) * amp);
            if (!jumpscare && Random.value < 0.4f) twitchTarget = Quaternion.Euler(0f, 0f, Random.Range(-12f, 12f));
        }
        twitchCurrent = Quaternion.Slerp(twitchCurrent, twitchTarget, dt * (jumpscare ? 40f : 22f));
        Set(head, headR, twitchCurrent);

        // --- челюсть
        float jawOpen = jumpscare ? 1f : (chasing ? 0.55f + Mathf.PerlinNoise(Time.time * 5f, 3f) * 0.4f : Mathf.PerlinNoise(Time.time * 0.8f, 7f) * 0.3f);
        Set(jaw, jawR, Quaternion.Euler(jawOpen * 38f, 0f, 0f));
    }

    void UpdateLeds(float dt)
    {
        if (ledRenderers == null || ledRenderers.Length == 0) return;
        ledGlitch -= dt;
        ledScroll += dt * ledScrollSpeed * (ledMode == 1 ? 2.2f : 1f);
        // строки текстуры: 0 — ДОБРО ПОЖАЛОВАТЬ, 1 — ПОКУПАТЕЛЬ ОБНАРУЖЕН, 2 — ОСТАНЬТЕСЬ С НАМИ, 3 — помехи
        int row = jumpscare ? 2 : (ledGlitch > 0f ? 3 : ledMode);
        float rowH = 1f / Mathf.Max(1, ledRows);
        float yOff = 1f - rowH * (row + 1);
        float intensity = jumpscare ? 3f : (ledGlitch > 0f ? Random.Range(0.2f, 2.5f) : 1.6f + Mathf.Sin(Time.time * 9f) * 0.2f);
        foreach (var r in ledRenderers)
        {
            if (r == null) continue;
            r.GetPropertyBlock(mpb);
            mpb.SetVector("_MainTex_ST", new Vector4(0.35f, rowH, ledScroll, yOff));
            mpb.SetFloat("_Intensity", intensity);
            r.SetPropertyBlock(mpb);
        }
    }

    static void Set(Transform t, Quaternion baseRot, Quaternion offset)
    {
        if (t != null) t.localRotation = baseRot * offset;
    }
}
