using System.Collections.Generic;
using UnityEngine;

public enum MonsterState { Dormant, Patrol, Investigate, Chase, Search, Kill }

/// <summary>
/// Мерчандайзер — сломанный манекен-промоутер ТЦ. Спит, пока GameManager его не разбудит.
/// Патрулирует, слышит шаги и двери, видит свет телефона, гонится, ищет, открывает двери.
/// Движется рвано, "с лагами": то скользит, то замирает и рывком догоняет позицию.
/// Не видит игрока в укрытии, если не заметил, как тот туда залез.
/// </summary>
[RequireComponent(typeof(CharacterController))]
public class MonsterAI : MonoBehaviour
{
    public static MonsterAI Instance { get; private set; }

    [Header("Ссылки")]
    public NavGrid grid;
    public Transform eyes;
    public Transform head;
    public Transform patrolRoot;
    public GameObject visualRoot;
    public MonsterAnimator animator;
    public Light eyeLight;

    [Header("Скорости")]
    public float patrolSpeed = 1.35f;
    public float investigateSpeed = 2.1f;
    public float chaseSpeed = 3.7f;
    public float chaseSpeedPerFuse = 0.14f;
    public float searchSpeed = 1.8f;
    public float turnSpeed = 540f;

    [Header("Чувства")]
    public float sightRange = 13f;
    public float flashlightSightBonus = 9f;
    public float sightAngle = 120f;
    public float proximitySense = 2.6f;
    public float hearingMultiplier = 1f;
    public float loseSightTime = 2.2f;
    public float searchDuration = 14f;
    public float catchDistance = 1.25f;

    [Header("Рваное движение")]
    [Range(0f, 1f)] public float lagChance = 0.35f;
    public Vector2 lagDuration = new Vector2(0.08f, 0.35f);

    [Header("Звук")]
    public AudioSource voice;
    public AudioSource sfx;
    public AudioClip[] stepClips;
    public AudioClip spottedClip;
    public AudioClip awakenClip;
    public AudioClip[] idleClips;

    public MonsterState State { get; private set; } = MonsterState.Dormant;
    public bool IsActive => State != MonsterState.Dormant;
    public bool IsChasing => State == MonsterState.Chase;

    CharacterController cc;
    Transform[] patrolPoints;
    readonly List<Vector3> path = new List<Vector3>();
    int pathIndex;
    Vector3 currentTarget;
    Vector3 lastKnownPlayerPos;
    float repathTimer;
    float lostTimer;
    float stateTimer;
    float searchTimer;
    float lookAroundTimer;
    float doorPause;
    float doorCheckTimer;
    float stuckTimer;
    Vector3 stuckAnchor;
    float verticalVel;
    float stepAccum;
    float idleSoundTimer;
    float spottedCooldown;
    float currentSpeed;
    float lagTimer;
    float lagCooldown;
    Vector3 lagAccum;
    bool sawPlayerHide;

    void Awake()
    {
        Instance = this;
        cc = GetComponent<CharacterController>();
        if (patrolRoot != null)
        {
            patrolPoints = new Transform[patrolRoot.childCount];
            for (int i = 0; i < patrolRoot.childCount; i++) patrolPoints[i] = patrolRoot.GetChild(i);
        }
        if (voice != null) { voice.spatialBlend = 1f; voice.loop = true; voice.rolloffMode = AudioRolloffMode.Linear; voice.maxDistance = 22f; voice.volume = 0f; }
        if (sfx != null) { sfx.spatialBlend = 1f; sfx.playOnAwake = false; sfx.rolloffMode = AudioRolloffMode.Linear; sfx.maxDistance = 26f; }
        SetVisible(false);
    }

    void OnEnable() { NoiseSystem.OnNoise += OnNoise; }
    void OnDisable() { NoiseSystem.OnNoise -= OnNoise; }

    void SetVisible(bool v)
    {
        if (visualRoot != null) visualRoot.SetActive(v);
        if (eyeLight != null) eyeLight.enabled = v;
        cc.enabled = v;
    }

    /// <summary>Разбудить: появляется в самой дальней от игрока точке патруля.</summary>
    public void Awaken()
    {
        if (State != MonsterState.Dormant) return;
        Vector3 pp = PlayerController.Instance != null ? PlayerController.Instance.transform.position : transform.position;
        if (patrolPoints != null && patrolPoints.Length > 0)
        {
            Transform far = patrolPoints[0];
            float best = -1f;
            foreach (var t in patrolPoints)
            {
                float d = (t.position - pp).sqrMagnitude;
                if (d > best) { best = d; far = t; }
            }
            transform.position = far.position;
        }
        SetVisible(true);
        if (voice != null && voice.clip != null) voice.Play();
        if (sfx != null && awakenClip != null) sfx.PlayOneShot(awakenClip, 1f);
        EnterPatrol();
        stateTimer = 4f; // стоит и "принюхивается"
    }

    float ChaseSpeed()
    {
        int fuses = GameManager.Instance != null ? GameManager.Instance.FusesCollected : 0;
        return chaseSpeed + chaseSpeedPerFuse * fuses;
    }

    void Update()
    {
        if (State == MonsterState.Dormant || State == MonsterState.Kill) return;
        var gm = GameManager.Instance;
        if (gm != null && (gm.State == GameState.Dead || gm.State == GameState.Won)) return;

        float dt = Time.deltaTime;
        spottedCooldown -= dt;
        doorPause -= dt;

        // если игрок прячется прямо на глазах во время погони — монстр это запоминает
        var pc = PlayerController.Instance;
        if (pc != null && !pc.IsHidden) sawPlayerHide = State == MonsterState.Chase && lostTimer < 0.6f;
        bool sees = CanSeePlayer();
        if (sees)
        {
            lastKnownPlayerPos = PlayerController.Instance.transform.position;
            lostTimer = 0f;
            if (State != MonsterState.Chase) EnterChase();
        }

        float speed = 0f;
        switch (State)
        {
            case MonsterState.Patrol:
                speed = patrolSpeed;
                if (stateTimer > 0f) { stateTimer -= dt; speed = 0f; break; }
                if (PathDone()) { stateTimer = Random.Range(1.5f, 4f); PickPatrolTarget(); }
                break;

            case MonsterState.Investigate:
                speed = investigateSpeed;
                if (PathDone())
                {
                    speed = 0f;
                    lookAroundTimer -= dt;
                    transform.Rotate(0f, Mathf.Sin(Time.time * 1.7f) * 90f * dt, 0f);
                    if (lookAroundTimer <= 0f) EnterSearch(currentTarget);
                }
                break;

            case MonsterState.Chase:
                speed = ChaseSpeed();
                if (!sees)
                {
                    lostTimer += dt;
                    if (lostTimer > loseSightTime && PathDone()) { EnterSearch(lastKnownPlayerPos); break; }
                }
                repathTimer -= dt;
                if (repathTimer <= 0f)
                {
                    repathTimer = 0.3f;
                    SetDestination(sees ? PlayerController.Instance.transform.position : lastKnownPlayerPos);
                }
                if (sees && TryCatch()) return;
                break;

            case MonsterState.Search:
                speed = searchSpeed;
                searchTimer -= dt;
                if (searchTimer <= 0f) { EnterPatrol(); break; }
                if (PathDone())
                {
                    if (stateTimer > 0f) { stateTimer -= dt; speed = 0f; transform.Rotate(0f, 70f * dt, 0f); }
                    else
                    {
                        stateTimer = Random.Range(1f, 2.5f);
                        if (grid != null) SetDestination(grid.RandomWalkableNear(lastKnownPlayerPos, 7f));
                    }
                }
                break;
        }

        if (doorPause > 0f) speed = 0f;
        Move(speed, dt);
        CheckDoors(dt);
        CheckStuck(dt);
        UpdateAudio(dt);

        if (animator != null)
        {
            animator.speed = currentSpeed;
            animator.chasing = State == MonsterState.Chase;
        }
    }

    // ---------------------------------------------------------------- состояния

    void EnterPatrol()
    {
        State = MonsterState.Patrol;
        PickPatrolTarget();
    }

    void EnterChase()
    {
        bool fresh = State != MonsterState.Chase;
        State = MonsterState.Chase;
        repathTimer = 0f;
        if (fresh && spottedCooldown <= 0f)
        {
            spottedCooldown = 12f;
            if (sfx != null && spottedClip != null) sfx.PlayOneShot(spottedClip, 1f);
            if (GameManager.Instance != null) GameManager.Instance.OnMonsterSpotted();
        }
    }

    void EnterInvestigate(Vector3 pos)
    {
        State = MonsterState.Investigate;
        currentTarget = pos;
        lookAroundTimer = Random.Range(2f, 4f);
        SetDestination(pos);
    }

    void EnterSearch(Vector3 around)
    {
        State = MonsterState.Search;
        lastKnownPlayerPos = around;
        searchTimer = searchDuration;
        stateTimer = 1.5f;
    }

    void PickPatrolTarget()
    {
        if (patrolPoints == null || patrolPoints.Length == 0) return;
        Vector3 pp = PlayerController.Instance != null ? PlayerController.Instance.transform.position : transform.position;
        Transform pick = patrolPoints[Random.Range(0, patrolPoints.Length)];

        // "поводок": чаще выбираем точки поближе к игроку, чтобы держать напряжение
        int fuses = GameManager.Instance != null ? GameManager.Instance.FusesCollected : 0;
        if (Random.value < 0.35f + fuses * 0.08f)
        {
            float best = float.MaxValue;
            foreach (var t in patrolPoints)
            {
                float d = Vector3.Distance(t.position, pp) + Random.Range(0f, 6f);
                if (d < best && Vector3.Distance(t.position, transform.position) > 3f) { best = d; pick = t; }
            }
        }
        SetDestination(pick.position);
    }

    void OnNoise(Vector3 pos, float radius)
    {
        if (!IsActive || State == MonsterState.Chase || State == MonsterState.Kill) return;
        float d = Vector3.Distance(pos, transform.position);
        if (d <= radius * hearingMultiplier) EnterInvestigate(pos);
    }

    // ---------------------------------------------------------------- чувства

    bool CanSeePlayer()
    {
        var p = PlayerController.Instance;
        if (p == null || eyes == null) return false;
        if (p.IsHidden) return sawPlayerHide && Vector3.Distance(transform.position, p.transform.position) < 25f;
        Vector3 eye = eyes.position;
        Vector3 target = p.EyePosition - Vector3.up * 0.25f;
        Vector3 to = target - eye;
        float dist = to.magnitude;

        float range = sightRange;
        if (Flashlight.Instance != null && Flashlight.Instance.IsLit) range += flashlightSightBonus;
        if (p.IsCrouching) range *= 0.55f;

        bool inCone = Vector3.Angle(transform.forward, to) < sightAngle * 0.5f;
        bool close = dist < proximitySense;
        if (dist > range || (!inCone && !close)) return false;

        if (Physics.Raycast(eye, to / dist, out RaycastHit hit, dist + 0.2f, ~0, QueryTriggerInteraction.Ignore))
            return hit.collider.GetComponentInParent<PlayerController>() != null;
        return true;
    }

    bool TryCatch()
    {
        var p = PlayerController.Instance;
        Vector3 a = transform.position; a.y = 0f;
        Vector3 b = p.transform.position; b.y = 0f;
        if (Vector3.Distance(a, b) > catchDistance) return false;
        State = MonsterState.Kill;
        lagTimer = 0f;
        if (voice != null) voice.Stop();
        if (GameManager.Instance != null) GameManager.Instance.PlayerCaught(this);
        return true;
    }

    // ---------------------------------------------------------------- движение

    void SetDestination(Vector3 dest)
    {
        currentTarget = dest;
        pathIndex = 0;
        if (grid == null || !grid.FindPath(transform.position, dest, path))
        {
            path.Clear();
            path.Add(dest);
        }
        // первая точка — наша же клетка, пропускаем
        if (path.Count > 1) pathIndex = 1;
    }

    bool PathDone() => pathIndex >= path.Count;

    void Move(float speed, float dt)
    {
        Vector3 move = Vector3.zero;
        if (!PathDone() && speed > 0f)
        {
            Vector3 target = path[pathIndex];
            Vector3 to = target - transform.position; to.y = 0f;
            if (to.magnitude < 0.3f)
            {
                pathIndex++;
            }
            else
            {
                Vector3 dir = to.normalized;
                Quaternion look = Quaternion.LookRotation(dir);
                transform.rotation = Quaternion.RotateTowards(transform.rotation, look, turnSpeed * dt);
                // не ломимся вперёд, пока не развернулись
                float facing = Mathf.Clamp01(Vector3.Dot(transform.forward, dir) * 1.5f);
                move = dir * speed * Mathf.Max(0.25f, facing);
            }
        }
        else if (State == MonsterState.Chase && PlayerController.Instance != null)
        {
            Vector3 to = PlayerController.Instance.transform.position - transform.position; to.y = 0f;
            if (to.sqrMagnitude > 0.01f)
                transform.rotation = Quaternion.RotateTowards(transform.rotation, Quaternion.LookRotation(to), turnSpeed * dt);
        }

        if (cc.isGrounded && verticalVel < 0f) verticalVel = -2f;
        verticalVel += -20f * dt;
        // "лаг": копим движение и потом отдаём рывком, как дёрганая аниматроника
        lagCooldown -= dt;
        if (lagTimer > 0f)
        {
            lagTimer -= dt;
            lagAccum += move * dt;
            if (lagTimer <= 0f && cc.enabled) { cc.Move(lagAccum); lagAccum = Vector3.zero; if (animator != null) animator.Glitch(); }
            if (cc.enabled) cc.Move(Vector3.up * verticalVel * dt);
        }
        else
        {
            if (lagCooldown <= 0f && move.sqrMagnitude > 0.01f)
            {
                lagCooldown = Random.Range(0.4f, 1.6f);
                if (Random.value < lagChance) { lagTimer = Random.Range(lagDuration.x, lagDuration.y); lagAccum = Vector3.zero; }
            }
            if (cc.enabled) cc.Move((move + Vector3.up * verticalVel) * dt);
        }
        if (animator != null) animator.frozen = lagTimer > 0f;

        Vector3 v = cc.velocity; v.y = 0f;
        currentSpeed = Mathf.Lerp(currentSpeed, v.magnitude, dt * 8f);

        stepAccum += currentSpeed * dt;
        if (stepAccum > 1.6f)
        {
            stepAccum = 0f;
            if (sfx != null && stepClips != null && stepClips.Length > 0)
            {
                sfx.pitch = Random.Range(0.75f, 0.9f);
                sfx.PlayOneShot(stepClips[Random.Range(0, stepClips.Length)], State == MonsterState.Chase ? 1f : 0.7f);
                sfx.pitch = 1f;
            }
            if (State == MonsterState.Chase) PlayerController.AddShake(ProximityShake());
        }
    }

    float ProximityShake()
    {
        if (PlayerController.Instance == null) return 0f;
        float d = Vector3.Distance(transform.position, PlayerController.Instance.transform.position);
        return Mathf.Clamp01(1f - d / 10f) * 0.12f;
    }

    void CheckDoors(float dt)
    {
        doorCheckTimer -= dt;
        if (doorCheckTimer > 0f) return;
        doorCheckTimer = 0.15f;
        Vector3 probe = transform.position + transform.forward * 0.9f + Vector3.up * 1f;
        var hits = Physics.OverlapSphere(probe, 0.75f, ~0, QueryTriggerInteraction.Ignore);
        foreach (var h in hits)
        {
            var door = h.GetComponentInParent<Door>();
            if (door == null || door.IsOpen || door.IsLocked) continue;
            bool slam = State == MonsterState.Chase;
            door.Open(transform.position, slam);
            doorPause = slam ? 0.35f : 0.9f;
            if (animator != null) animator.Lunge();
            break;
        }
    }

    void CheckStuck(float dt)
    {
        stuckTimer += dt;
        if (stuckTimer < 1.2f) return;
        bool trying = !PathDone() && doorPause <= 0f && State != MonsterState.Kill;
        if (trying && Vector3.Distance(stuckAnchor, transform.position) < 0.2f)
        {
            // застряли — перестраиваем путь, при повторе сбрасываем цель
            if (State == MonsterState.Chase) repathTimer = 0f;
            else if (State == MonsterState.Patrol) PickPatrolTarget();
            else SetDestination(currentTarget);
            pathIndex = Mathf.Min(pathIndex + 1, path.Count);
        }
        stuckAnchor = transform.position;
        stuckTimer = 0f;
    }

    void UpdateAudio(float dt)
    {
        if (voice != null)
        {
            // джингл ускоряется, когда он рядом
            float near = 0f;
            if (PlayerController.Instance != null)
                near = Mathf.Clamp01(1f - Vector3.Distance(transform.position, PlayerController.Instance.transform.position) / 16f);
            float target = State == MonsterState.Chase ? 0.95f : 0.5f;
            voice.volume = Mathf.MoveTowards(voice.volume, target, dt);
            float wobble = (Mathf.PerlinNoise(Time.time * 2f, 5f) - 0.5f) * 0.08f;
            voice.pitch = Mathf.MoveTowards(voice.pitch, 0.85f + near * 0.45f + (State == MonsterState.Chase ? 0.15f : 0f) + wobble, dt);
        }
        idleSoundTimer -= dt;
        if (idleSoundTimer <= 0f)
        {
            idleSoundTimer = Random.Range(7f, 16f);
            if (State != MonsterState.Chase && sfx != null && idleClips != null && idleClips.Length > 0)
                sfx.PlayOneShot(idleClips[Random.Range(0, idleClips.Length)], 0.8f);
        }
        if (eyeLight != null) eyeLight.intensity = (State == MonsterState.Chase ? 1.4f : 0.7f) * (0.8f + Mathf.PerlinNoise(Time.time * 8f, 0f) * 0.4f);
        if (animator != null) animator.ledMode = State == MonsterState.Chase ? 1 : 0;
    }

    // ---------------------------------------------------------------- скример

    /// <summary>Ставит монстра вплотную к камере для скримера.</summary>
    public void PlaceForJumpscare(Transform cam)
    {
        cc.enabled = false;
        Vector3 fwd = cam.forward; fwd.y = 0f;
        if (fwd.sqrMagnitude < 0.01f) fwd = cam.parent != null ? cam.parent.forward : Vector3.forward;
        fwd.Normalize();

        transform.rotation = Quaternion.LookRotation(-fwd);
        if (animator != null) animator.jumpscare = true;
        Vector3 headOffset = (head != null ? head.position : transform.position + Vector3.up * 2.2f) - transform.position;
        Vector3 desiredHead = cam.position + fwd * 0.62f + Vector3.up * 0.02f;
        transform.position = desiredHead - headOffset;
    }

    void OnDrawGizmosSelected()
    {
        Gizmos.color = Color.red;
        Gizmos.DrawWireSphere(transform.position, catchDistance);
        Gizmos.color = new Color(1f, 0.5f, 0f, 0.4f);
        Gizmos.DrawWireSphere(transform.position, sightRange);
        if (path.Count > 1)
        {
            Gizmos.color = Color.magenta;
            for (int i = 1; i < path.Count; i++) Gizmos.DrawLine(path[i - 1] + Vector3.up * 0.2f, path[i] + Vector3.up * 0.2f);
        }
    }
}
