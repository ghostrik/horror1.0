using UnityEngine;
using UnityEngine.SceneManagement;

/// <summary>Главное меню: медленный пролёт камеры по тёмному атриуму + заголовок и кнопки.</summary>
public class MainMenu : MonoBehaviour
{
    public string gameScene = "Mall";
    public Transform cameraTransform;
    public float driftAmount = 0.6f;
    public float driftSpeed = 0.12f;
    public AudioSource music;

    bool showControls;
    float fadeIn = 1f;
    float leaving = -1f;
    Vector3 camBase;
    Quaternion camRot;
    GUIStyle sTitle, sSub, sButton, sText;
    Texture2D white;

    void Start()
    {
        Time.timeScale = 1f;
        AudioListener.pause = false;
        HInput.LockCursor(false);
        white = Texture2D.whiteTexture;
        if (cameraTransform != null) { camBase = cameraTransform.position; camRot = cameraTransform.rotation; }
        if (music != null) { music.spatialBlend = 0f; music.loop = true; if (!music.isPlaying && music.clip != null) music.Play(); }
    }

    void Update()
    {
        fadeIn = Mathf.MoveTowards(fadeIn, 0f, Time.deltaTime * 0.5f);
        if (cameraTransform != null)
        {
            float t = Time.time * driftSpeed;
            cameraTransform.position = camBase + new Vector3(Mathf.Sin(t) * driftAmount, Mathf.Sin(t * 1.3f) * 0.1f, Mathf.Cos(t * 0.7f) * driftAmount * 0.5f);
            cameraTransform.rotation = camRot * Quaternion.Euler(Mathf.Sin(t * 0.9f) * 1.5f, Mathf.Sin(t * 0.6f) * 4f, 0f);
        }
        if (leaving >= 0f)
        {
            leaving += Time.deltaTime;
            if (music != null) music.volume = Mathf.Max(0f, 1f - leaving);
            if (leaving > 1.2f) SceneManager.LoadScene(gameScene);
        }
    }

    void OnGUI()
    {
        if (sTitle == null)
        {
            sTitle = new GUIStyle(GUI.skin.label) { fontSize = 110, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleLeft };
            sTitle.normal.textColor = new Color(0.92f, 0.9f, 0.86f);
            sSub = new GUIStyle(GUI.skin.label) { fontSize = 32, fontStyle = FontStyle.Italic, alignment = TextAnchor.MiddleLeft };
            sSub.normal.textColor = new Color(0.8f, 0.3f, 0.3f);
            sButton = new GUIStyle(GUI.skin.label) { fontSize = 38, alignment = TextAnchor.MiddleLeft };
            sButton.normal.textColor = new Color(0.75f, 0.75f, 0.72f);
            sButton.hover.textColor = Color.white;
            sText = new GUIStyle(GUI.skin.label) { fontSize = 26, alignment = TextAnchor.UpperLeft, wordWrap = true, richText = true };
            sText.normal.textColor = new Color(0.85f, 0.85f, 0.82f);
        }

        float scale = Screen.height / 1080f;
        float W = Screen.width / scale, H = 1080f;
        GUI.matrix = Matrix4x4.Scale(new Vector3(scale, scale, 1f));

        // затемнение слева под текст
        for (int i = 0; i < 16; i++)
        {
            GUI.color = new Color(0f, 0f, 0f, 0.05f);
            GUI.DrawTexture(new Rect(0, 0, 60 + i * 55, H), white);
        }
        GUI.color = Color.white;

        float jitter = Random.value < 0.03f ? Random.Range(-6f, 6f) : 0f;
        GUI.Label(new Rect(120 + jitter, 170, 1400, 150), "ГАЛАКТИКА", sTitle);
        GUI.Label(new Rect(126, 300, 1200, 50), "ночь в закрытом торговом центре", sSub);

        float y = 470;
        if (!showControls)
        {
            if (Button(new Rect(120, y, 600, 60), "Начать запись")) leaving = 0f;
            if (Button(new Rect(120, y + 75, 600, 60), "Управление")) showControls = true;
            if (Button(new Rect(120, y + 150, 600, 60), "Выйти")) Application.Quit();
        }
        else
        {
            GUI.Label(new Rect(120, y, 900, 420),
                "<b>WASD</b> — идти     <b>Shift</b> — бежать     <b>Ctrl / C</b> — присесть\n" +
                "<b>Мышь</b> — осмотреться     <b>F</b> — фонарик телефона\n" +
                "<b>E / ЛКМ</b> — взаимодействовать, спрятаться, вылезти\n" +
                "<b>Tab</b> — текущая цель     <b>Esc</b> — пауза и настройки\n\n" +
                "<i>Свет телефона выдаёт тебя. Бег слышно издалека.\n" +
                "Если он не видел, куда ты спрятался, — он тебя не найдёт.</i>", sText);
            if (Button(new Rect(120, y + 330, 600, 60), "Назад")) showControls = false;
        }

        GUI.color = new Color(1f, 1f, 1f, 0.35f);
        GUI.Label(new Rect(120, H - 70, 900, 40), "Тестовая демо-версия · зоны 1–2 из 5", sText);
        GUI.color = Color.white;

        float black = Mathf.Max(fadeIn, leaving >= 0f ? Mathf.Clamp01(leaving) : 0f);
        if (black > 0f)
        {
            GUI.color = new Color(0f, 0f, 0f, black);
            GUI.DrawTexture(new Rect(0, 0, W, H), white);
            GUI.color = Color.white;
        }
    }

    bool Button(Rect r, string text)
    {
        bool hover = r.Contains(Event.current.mousePosition);
        return GUI.Button(r, (hover ? "›  " : "   ") + text, sButton);
    }
}
