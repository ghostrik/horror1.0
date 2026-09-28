using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;

public enum GameState { Intro, Playing, Reading, Paused, Dead, Won }

/// <summary>
/// Сердце демо: сюжетные этапы, цели, HUD, чтение находок, пауза, смерть (скример), финал.
/// Весь интерфейс на IMGUI — никаких зависимостей от пакетов UI.
/// </summary>
public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    [Header("Ссылки")]
    public PlayerController player;
    public MonsterAI monster;
    public HorrorPostFX postFX;
    public Apparition firstFuseApparition;

    [Header("Прогресс")]
    public int fusesRequired = 3;
    public int awakenMonsterAtFuse = 2;

    [Header("Звук")]
    public AudioSource musicSource;
    public AudioSource heartbeatSource;
    public AudioSource uiSource;
    public AudioClip paperClip;
    public AudioClip stingerClip;
    public AudioClip screamClip;
    public AudioClip winClip;
    public AudioClip fuseClip;

    [Header("Интерфейс")]
    public Texture2D paperTexture;
    public Texture2D phoneIcon;
    public string menuScene = "MainMenu";

    [Header("Интро")]
    [TextArea(2, 4)]
    public string[] introLines =
    {
        "ТЦ «Галактика». Закрыт шесть лет назад.",
        "Ребят я отправил домой сам. «Одному будет страшнее, зрителям зайдёт».",
        "Решётку закрыл изнутри — для антуража.",
        "Ночь. 02:47. Запись пошла.",
    };

    public GameState State { get; private set; } = GameState.Intro;
    public bool IsPlaying => State == GameState.Playing;
    public int FusesCollected { get; private set; }
    public bool PowerRestored { get; private set; }
    public int LoreFound { get; private set; }
    public int LoreTotal { get; private set; }
    public float Fear { get; private set; }
    public float MonsterProximity01 { get; private set; }

    string objective = "";
    float objectiveFlash;
    string message = "";
    float messageTimer;
    string subtitle = "";
    float subtitleTimer;
    NotePickup reading;
    float blackFade = 1f;
    float whiteFade;
    string introText = "";
    float introAlpha;
    float playTime;
    int deaths;
    float volume = 1f;
    bool styles;
    GUIStyle sTitle, sBody, sHint, sMsg, sSub, sBig, sSmall, sPaperTitle, sPaperBody, sButton;
    Texture2D white;
    bool gratePrompted;

    void Awake()
    {
        Instance = this;
        Time.timeScale = 1f;
        QualitySettings.pixelLightCount = Mathf.Max(QualitySettings.pixelLightCount, 8);
        QualitySettings.shadowDistance = 30f;
        volume = PlayerPrefs.GetFloat("hb_volume", 1f);
        AudioListener.volume = volume;
        white = Texture2D.whiteTexture;
        LoreTotal = FindObjectsByType<NotePickup>(FindObjectsSortMode.None).Length;
        if (heartbeatSource != null) { heartbeatSource.spatialBlend = 0f; heartbeatSource.loop = true; heartbeatSource.volume = 0f; if (heartbeatSource.clip != null) heartbeatSource.Play(); }
        if (musicSource != null) { musicSource.spatialBlend = 0f; musicSource.loop = true; }
        if (uiSource != null) uiSource.spatialBlend = 0f;
    }

    void Start()
    {
        StartCoroutine(IntroRoutine());
    }

    IEnumerator IntroRoutine()
    {
        HInput.LockCursor(true);
        State = GameState.Intro;
        blackFade = 1f;
        if (player != null) player.CanControl = false;

        foreach (var line in introLines)
        {
            introText = line;
            for (float t = 0; t < 1f; t += Time.deltaTime * 1.5f) { introAlpha = t; if (Skip()) break; yield return null; }
            introAlpha = 1f;
            for (float t = 0; t < 2.6f; t += Time.deltaTime) { if (Skip()) break; yield return null; }
            for (float t = 1; t > 0f; t -= Time.deltaTime * 2f) { introAlpha = t; yield return null; }
            introAlpha = 0f;
            yield return null;
        }
        introText = "";
        State = GameState.Playing;
        if (player != null) player.CanControl = true;
        for (float t = 1; t > 0f; t -= Time.deltaTime * 0.5f) { blackFade = t; yield return null; }
        blackFade = 0f;

        SetObjective("Осмотреться. Снять пару планов для ролика.");
        yield return new WaitForSeconds(2f);
        ShowMessage("[F] — фонарик телефона.  [Shift] — бег.  [Ctrl] — присесть.", 5f);
        yield return new WaitForSeconds(6f);
        ShowMessage("[E] — взаимодействовать.  [Tab] — текущая цель.", 4f);
    }

    bool Skip() => HInput.KeyDown(KeyCode.Space) || HInput.KeyDown(KeyCode.Return) || HInput.KeyDown(KeyCode.Escape);

    // ------------------------------------------------------------------ сюжет

    public void SetObjective(string text)
    {
        objective = text;
        objectiveFlash = 5f;
    }

    public void ShowMessage(string text, float duration = 3.5f)
    {
        message = text;
        messageTimer = duration;
    }

    public void ShowSubtitle(string text, float duration = 5f)
    {
        subtitle = text;
        subtitleTimer = duration;
    }

    /// <summary>Игрок впервые дёрнул решётку.</summary>
    public void OnGrateJammed()
    {
        if (gratePrompted) return;
        gratePrompted = true;
        SetObjective("Найти другой выход. Говорят, через гипермаркет есть техкоридор.");
    }

    public void OnFuseCollected()
    {
        FusesCollected++;
        if (uiSource != null && fuseClip != null) uiSource.PlayOneShot(fuseClip, 0.8f);
        if (FusesCollected < fusesRequired)
            SetObjective($"Найти предохранители для щитка гипермаркета ({FusesCollected}/{fusesRequired}).");
        else
            SetObjective("Все предохранители у меня. Щиток — в подсобке гипермаркета.");

        if (FusesCollected == 1)
        {
            ShowMessage("Предохранитель. Щиток гипермаркета должен быть где-то в подсобке.", 4f);
            if (firstFuseApparition != null) firstFuseApparition.Show();
            if (PASystem.Instance != null) PASystem.Instance.Announce(2);
        }
        if (FusesCollected == awakenMonsterAtFuse && monster != null)
            StartCoroutine(AwakenRoutine());
    }

    IEnumerator AwakenRoutine()
    {
        yield return new WaitForSeconds(1.5f);
        foreach (var l in FlickerLight.All) if (l != null) l.ForceOff(2.5f);
        PlayerController.AddShake(0.5f);
        if (uiSource != null && stingerClip != null) uiSource.PlayOneShot(stingerClip, 0.9f);
        monster.Awaken();
        yield return new WaitForSeconds(1.2f);
        ShowMessage("Это был не звук вентиляции. Здесь кто-то есть.", 4f);
    }

    public void OnPowerRestored()
    {
        PowerRestored = true;
        SetObjective("Рольставня в техкоридор открывается. БЕГИ!");
        ShowMessage("Свет! ...и он точно это услышал.", 3.5f);
        PlayerController.AddShake(0.3f);
    }

    public void OnMonsterSpotted()
    {
        if (uiSource != null && stingerClip != null) uiSource.PlayOneShot(stingerClip, 1f);
        PlayerController.AddShake(0.35f);
        if (postFX != null) postFX.flash = Mathf.Max(postFX.flash, 0.6f);
    }

    public void ReadNote(NotePickup note)
    {
        if (!IsPlaying) return;
        reading = note;
        State = GameState.Reading;
        if (uiSource != null && paperClip != null) uiSource.PlayOneShot(paperClip, 0.8f);
    }

    void CloseNote()
    {
        if (reading != null && !reading.Collected)
        {
            reading.Collect();
            LoreFound++;
            ShowMessage($"Находки: {LoreFound}/{LoreTotal}", 2f);
        }
        reading = null;
        State = GameState.Playing;
    }

    public void PlayerCaught(MonsterAI m)
    {
        if (State == GameState.Dead || State == GameState.Won) return;
        if (State == GameState.Reading) reading = null;
        State = GameState.Dead;
        deaths++;
        StartCoroutine(DeathRoutine(m));
    }

    IEnumerator DeathRoutine(MonsterAI m)
    {
        player.CanControl = false;
        player.CanLook = false;
        var hide = FindObjectsByType<HidingSpot>(FindObjectsSortMode.None);
        foreach (var h in hide) if (h.Occupied) h.Leave();

        Transform cam = player.cameraTransform;
        m.PlaceForJumpscare(cam);
        Transform head = m.head != null ? m.head : m.transform;

        if (uiSource != null && screamClip != null) uiSource.PlayOneShot(screamClip, 1f);
        if (musicSource != null) musicSource.Stop();
        if (heartbeatSource != null) heartbeatSource.volume = 1f;

        // резкий поворот к лицу
        Quaternion from = cam.rotation;
        for (float t = 0; t < 1f; t += Time.deltaTime * 9f)
        {
            Quaternion to = Quaternion.LookRotation(head.position - cam.position);
            player.SetLookRotation(Quaternion.Slerp(from, to, t));
            yield return null;
        }
        float dur = 1.5f;
        for (float t = 0; t < dur; t += Time.deltaTime)
        {
            Quaternion to = Quaternion.LookRotation(head.position - cam.position);
            player.SetLookRotation(to);
            PlayerController.AddShake(0.25f);
            if (postFX != null) { postFX.flash = 1f; postFX.fear = 1f; }
            yield return null;
        }
        blackFade = 1f;
        if (heartbeatSource != null) heartbeatSource.Stop();
        yield return new WaitForSeconds(0.8f);
        HInput.LockCursor(false);
    }

    public void ReachedExit()
    {
        if (State != GameState.Playing) return;
        State = GameState.Won;
        StartCoroutine(WinRoutine());
    }

    IEnumerator WinRoutine()
    {
        player.CanControl = false;
        if (uiSource != null && winClip != null) uiSource.PlayOneShot(winClip, 1f);
        for (float t = 0; t < 1f; t += Time.deltaTime * 0.6f) { whiteFade = t; yield return null; }
        whiteFade = 1f;
        yield return new WaitForSeconds(0.5f);
        for (float t = 1; t > 0f; t -= Time.deltaTime) { whiteFade = t; blackFade = 1f - t; yield return null; }
        whiteFade = 0f;
        blackFade = 1f;
        HInput.LockCursor(false);
    }

    // ------------------------------------------------------------------ цикл

    void Update()
    {
        float dt = Time.unscaledDeltaTime;
        messageTimer -= dt;
        subtitleTimer -= dt;
        objectiveFlash -= dt;

        switch (State)
        {
            case GameState.Playing:
                playTime += Time.deltaTime;
                if (HInput.KeyDown(KeyCode.Escape)) SetPaused(true);
                if (HInput.KeyDown(KeyCode.Tab)) objectiveFlash = 4f;
                break;
            case GameState.Reading:
                if (HInput.KeyDown(KeyCode.E) || HInput.KeyDown(KeyCode.Escape) || HInput.KeyDown(KeyCode.Mouse0)) CloseNote();
                break;
            case GameState.Paused:
                if (HInput.KeyDown(KeyCode.Escape)) SetPaused(false);
                break;
            case GameState.Dead:
            case GameState.Won:
                if (blackFade >= 1f && HInput.KeyDown(KeyCode.R)) Restart();
                break;
        }

        UpdateFear(Time.deltaTime);
    }

    void UpdateFear(float dt)
    {
        float prox = 0f;
        float fearTarget = 0f;
        if (monster != null && monster.IsActive && player != null && State != GameState.Won)
        {
            float d = Vector3.Distance(monster.transform.position, player.transform.position);
            prox = Mathf.Clamp01(1f - (d - 2f) / 14f);
            fearTarget = prox * 0.8f + (monster.IsChasing ? 0.35f : 0f);
        }
        MonsterProximity01 = prox;
        if (State != GameState.Dead) Fear = Mathf.MoveTowards(Fear, Mathf.Clamp01(fearTarget), dt * 0.6f);

        if (heartbeatSource != null && State != GameState.Dead)
        {
            heartbeatSource.volume = Mathf.Clamp01(Fear * 1.1f) * 0.9f;
            heartbeatSource.pitch = 0.85f + Fear * 0.55f;
        }
        if (postFX != null && State != GameState.Dead)
        {
            postFX.fear = Fear;
            postFX.flash = Mathf.MoveTowards(postFX.flash, 0f, dt * 1.5f);
        }
    }

    void SetPaused(bool p)
    {
        State = p ? GameState.Paused : GameState.Playing;
        Time.timeScale = p ? 0f : 1f;
        AudioListener.pause = p;
        HInput.LockCursor(!p);
    }

    void Restart()
    {
        Time.timeScale = 1f;
        AudioListener.pause = false;
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
    }

    void ToMenu()
    {
        Time.timeScale = 1f;
        AudioListener.pause = false;
        if (Application.CanStreamedLevelBeLoaded(menuScene)) SceneManager.LoadScene(menuScene);
        else Restart();
    }

    void OnDestroy()
    {
        Time.timeScale = 1f;
        AudioListener.pause = false;
    }

    // ------------------------------------------------------------------ интерфейс

    void BuildStyles()
    {
        if (styles) return;
        styles = true;
        sTitle = new GUIStyle(GUI.skin.label) { fontSize = 64, alignment = TextAnchor.MiddleCenter, fontStyle = FontStyle.Bold, richText = true };
        sBig = new GUIStyle(sTitle) { fontSize = 90 };
        sBody = new GUIStyle(GUI.skin.label) { fontSize = 30, alignment = TextAnchor.MiddleCenter, wordWrap = true, richText = true };
        sHint = new GUIStyle(GUI.skin.label) { fontSize = 24, alignment = TextAnchor.MiddleCenter, richText = true };
        sMsg = new GUIStyle(GUI.skin.label) { fontSize = 28, alignment = TextAnchor.MiddleCenter, wordWrap = true, richText = true };
        sSub = new GUIStyle(sMsg) { fontSize = 26, fontStyle = FontStyle.Italic };
        sSmall = new GUIStyle(GUI.skin.label) { fontSize = 22, alignment = TextAnchor.UpperLeft, wordWrap = true, richText = true };
        sPaperTitle = new GUIStyle(GUI.skin.label) { fontSize = 34, alignment = TextAnchor.UpperCenter, fontStyle = FontStyle.Bold, wordWrap = true };
        sPaperTitle.normal.textColor = new Color(0.12f, 0.1f, 0.08f);
        sPaperBody = new GUIStyle(GUI.skin.label) { fontSize = 25, alignment = TextAnchor.UpperLeft, wordWrap = true, fontStyle = FontStyle.Italic, richText = true };
        sPaperBody.normal.textColor = new Color(0.15f, 0.12f, 0.1f);
        sButton = new GUIStyle(GUI.skin.button) { fontSize = 28 };
    }

    void OnGUI()
    {
        BuildStyles();
        float scale = Screen.height / 1080f;
        float W = Screen.width / scale, H = 1080f;
        GUI.matrix = Matrix4x4.Scale(new Vector3(scale, scale, 1f));

        if (State == GameState.Playing || State == GameState.Reading) DrawHUD(W, H);
        if (State == GameState.Reading) DrawNote(W, H);

        // затемнения
        if (whiteFade > 0f) { GUI.color = new Color(1f, 1f, 1f, whiteFade); GUI.DrawTexture(new Rect(0, 0, W, H), white); }
        if (blackFade > 0f) { GUI.color = new Color(0f, 0f, 0f, blackFade); GUI.DrawTexture(new Rect(0, 0, W, H), white); }
        GUI.color = Color.white;

        if (!string.IsNullOrEmpty(introText))
            Shadow(new Rect(W * 0.1f, H * 0.4f, W * 0.8f, 200), introText, sBody, new Color(0.9f, 0.9f, 0.88f, introAlpha));

        if (State == GameState.Paused) DrawPause(W, H);
        if (State == GameState.Dead && blackFade >= 1f) DrawDeath(W, H);
        if (State == GameState.Won && blackFade >= 1f) DrawWin(W, H);
    }

    void DrawHUD(float W, float H)
    {
        // прицел
        bool hover = Interactor.Instance != null && Interactor.Instance.Current != null;
        float cs = hover ? 10f : 4f;
        GUI.color = new Color(1f, 1f, 1f, hover ? 0.9f : 0.35f);
        GUI.DrawTexture(new Rect(W * 0.5f - cs * 0.5f, H * 0.5f - cs * 0.5f, cs, cs), white);
        GUI.color = Color.white;
        if (hover) Shadow(new Rect(W * 0.5f - 300, H * 0.5f + 24, 600, 40), Interactor.Instance.Current.Prompt, sHint, new Color(1f, 1f, 1f, 0.9f));

        // "интерфейс камеры телефона": REC и время
        float blink = Mathf.Repeat(Time.time, 1.2f) < 0.7f ? 1f : 0f;
        GUI.color = new Color(0.9f, 0.1f, 0.1f, 0.85f * blink);
        GUI.DrawTexture(new Rect(40, 40, 18, 18), white);
        GUI.color = Color.white;
        int secs = Mathf.FloorToInt(playTime);
        Shadow(new Rect(68, 30, 400, 40), $"REC  {secs / 3600:00}:{(secs / 60) % 60:00}:{secs % 60:00}", sSmall, new Color(1f, 1f, 1f, 0.75f));

        // батарея телефона
        if (Flashlight.Instance != null)
        {
            float b = Flashlight.Instance.battery;
            float x = W - 170, y = 36;
            GUI.color = new Color(1f, 1f, 1f, 0.6f);
            Frame(new Rect(x, y, 90, 34), 2f);
            GUI.DrawTexture(new Rect(x + 90, y + 10, 6, 14), white);
            GUI.color = b < 0.2f ? new Color(1f, 0.2f, 0.15f, 0.9f) : new Color(1f, 1f, 1f, 0.75f);
            GUI.DrawTexture(new Rect(x + 5, y + 5, 80 * b, 24), white);
            GUI.color = Color.white;
            Shadow(new Rect(x - 110, y, 100, 34), Mathf.RoundToInt(b * 100) + "%", sHint, new Color(1f, 1f, 1f, 0.7f));
        }

        // предохранители
        if (FusesCollected > 0 && !PowerRestored)
            Shadow(new Rect(W - 420, 80, 390, 36), $"Предохранители: {FusesCollected}/{fusesRequired}", new GUIStyle(sSmall) { alignment = TextAnchor.UpperRight }, new Color(1f, 0.85f, 0.4f, 0.85f));

        // выносливость
        if (player != null && player.Stamina01 < 0.99f)
        {
            float w = 260f;
            GUI.color = new Color(1f, 1f, 1f, 0.15f);
            GUI.DrawTexture(new Rect(W * 0.5f - w * 0.5f, H - 60, w, 5), white);
            GUI.color = new Color(1f, 1f, 1f, 0.6f);
            GUI.DrawTexture(new Rect(W * 0.5f - w * 0.5f, H - 60, w * player.Stamina01, 5), white);
            GUI.color = Color.white;
        }

        if (player != null && player.IsHidden)
            Shadow(new Rect(W * 0.5f - 200, H - 120, 400, 40), "— в укрытии —", sHint, new Color(0.7f, 0.9f, 1f, 0.6f));

        // цель
        if (objectiveFlash > 0f && !string.IsNullOrEmpty(objective))
        {
            float a = Mathf.Clamp01(objectiveFlash);
            Shadow(new Rect(40, 90, 700, 120), "<b>ЦЕЛЬ</b>\n" + objective, sSmall, new Color(1f, 1f, 1f, 0.85f * a));
        }

        // сообщения и субтитры
        if (messageTimer > 0f)
            Shadow(new Rect(W * 0.5f - 600, H - 230, 1200, 80), message, sMsg, new Color(1f, 1f, 1f, Mathf.Clamp01(messageTimer)));
        if (subtitleTimer > 0f)
            Shadow(new Rect(W * 0.5f - 700, H - 150, 1400, 80), subtitle, sSub, new Color(0.85f, 0.95f, 1f, Mathf.Clamp01(subtitleTimer)));
    }

    void DrawNote(float W, float H)
    {
        if (reading == null) return;
        GUI.color = new Color(0f, 0f, 0f, 0.75f);
        GUI.DrawTexture(new Rect(0, 0, W, H), white);
        GUI.color = Color.white;
        float pw = 760, ph = 900;
        Rect r = new Rect(W * 0.5f - pw * 0.5f, H * 0.5f - ph * 0.5f, pw, ph);
        if (paperTexture != null) GUI.DrawTexture(r, paperTexture, ScaleMode.StretchToFill);
        else { GUI.color = new Color(0.86f, 0.82f, 0.7f); GUI.DrawTexture(r, white); GUI.color = Color.white; }
        GUI.Label(new Rect(r.x + 60, r.y + 60, pw - 120, 60), reading.title, sPaperTitle);
        GUI.Label(new Rect(r.x + 70, r.y + 150, pw - 140, ph - 230), reading.body, sPaperBody);
        Shadow(new Rect(W * 0.5f - 200, r.yMax + 10, 400, 40), "[E] Закрыть", sHint, Color.white);
    }

    void DrawPause(float W, float H)
    {
        GUI.color = new Color(0f, 0f, 0f, 0.8f);
        GUI.DrawTexture(new Rect(0, 0, W, H), white);
        GUI.color = Color.white;
        Shadow(new Rect(0, 180, W, 100), "ПАУЗА", sTitle, new Color(0.9f, 0.9f, 0.9f));

        float bx = W * 0.5f - 220, by = 340;
        if (GUI.Button(new Rect(bx, by, 440, 64), "Продолжить", sButton)) SetPaused(false);

        GUI.Label(new Rect(bx, by + 90, 440, 40), $"Чувствительность мыши: {player.mouseSensitivity:0.0}", sHint);
        float sens = GUI.HorizontalSlider(new Rect(bx, by + 135, 440, 30), player.mouseSensitivity, 0.3f, 6f);
        if (!Mathf.Approximately(sens, player.mouseSensitivity)) { player.mouseSensitivity = sens; PlayerPrefs.SetFloat("hb_sensitivity", sens); }

        GUI.Label(new Rect(bx, by + 170, 440, 40), $"Громкость: {Mathf.RoundToInt(volume * 100)}%", sHint);
        float vol = GUI.HorizontalSlider(new Rect(bx, by + 215, 440, 30), volume, 0f, 1f);
        if (!Mathf.Approximately(vol, volume)) { volume = vol; AudioListener.volume = vol; PlayerPrefs.SetFloat("hb_volume", vol); }

        if (GUI.Button(new Rect(bx, by + 270, 440, 64), "Начать заново", sButton)) Restart();
        if (GUI.Button(new Rect(bx, by + 350, 440, 64), "В главное меню", sButton)) ToMenu();
        if (GUI.Button(new Rect(bx, by + 430, 440, 64), "Выйти из игры", sButton)) Application.Quit();
    }

    void DrawDeath(float W, float H)
    {
        Shadow(new Rect(0, H * 0.3f, W, 140), "<color=#b01010>ОБСЛУЖИВАНИЕ ЗАВЕРШЕНО</color>", sBig, Color.white);
        Shadow(new Rect(0, H * 0.3f + 150, W, 60), "Мерчандайзер нашёл покупателя.", sBody, new Color(0.8f, 0.8f, 0.8f));
        float bx = W * 0.5f - 220, by = H * 0.6f;
        if (GUI.Button(new Rect(bx, by, 440, 64), "[R] Ещё раз", sButton)) Restart();
        if (GUI.Button(new Rect(bx, by + 80, 440, 64), "В главное меню", sButton)) ToMenu();
    }

    void DrawWin(float W, float H)
    {
        Shadow(new Rect(0, H * 0.25f, W, 120), "КОНЕЦ ДЕМО", sBig, new Color(0.95f, 0.95f, 0.9f));
        int secs = Mathf.FloorToInt(playTime);
        Shadow(new Rect(0, H * 0.25f + 140, W, 160),
            $"Ты выбрался в технический коридор.\nВпереди — развлекательный этаж, кинотеатр и подвал.\n\nВремя: {secs / 60}:{secs % 60:00}   Находки: {LoreFound}/{LoreTotal}   Смертей: {deaths}",
            sBody, new Color(0.8f, 0.8f, 0.8f));
        float bx = W * 0.5f - 220, by = H * 0.65f;
        if (GUI.Button(new Rect(bx, by, 440, 64), "[R] Сыграть снова", sButton)) Restart();
        if (GUI.Button(new Rect(bx, by + 80, 440, 64), "В главное меню", sButton)) ToMenu();
    }

    void Frame(Rect r, float t)
    {
        GUI.DrawTexture(new Rect(r.x, r.y, r.width, t), white);
        GUI.DrawTexture(new Rect(r.x, r.yMax - t, r.width, t), white);
        GUI.DrawTexture(new Rect(r.x, r.y, t, r.height), white);
        GUI.DrawTexture(new Rect(r.xMax - t, r.y, t, r.height), white);
    }

    static void Shadow(Rect r, string text, GUIStyle style, Color color)
    {
        var old = style.normal.textColor;
        style.normal.textColor = new Color(0f, 0f, 0f, color.a * 0.8f);
        GUI.Label(new Rect(r.x + 2, r.y + 2, r.width, r.height), text, style);
        style.normal.textColor = color;
        GUI.Label(r, text, style);
        style.normal.textColor = old;
    }
}
