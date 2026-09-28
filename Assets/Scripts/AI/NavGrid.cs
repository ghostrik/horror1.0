using System.Collections.Generic;
using UnityEngine;

/// <summary>
/// Сетка проходимости для монстра. Запекается при старте по реальным коллайдерам сцены,
/// поэтому если перестроить уровень в редакторе — монстр сам подстроится.
/// Двери считаются проходимыми (монстр их открывает).
/// A* с 8 направлениями + сглаживание пути.
/// </summary>
public class NavGrid : MonoBehaviour
{
    public Vector3 origin = Vector3.zero;
    public int width = 90;
    public int depth = 66;
    public float cellSize = 0.5f;
    public float agentRadius = 0.3f;
    public float checkBottom = 0.35f;
    public float checkTop = 1.8f;
    public bool drawGizmos = true;

    bool[] walkable;
    bool baked;

    // A* буферы
    float[] gCost;
    int[] parent;
    int[] heapIndex;
    int[] stamp;
    int searchId;
    readonly List<int> openHeap = new List<int>();
    float[] fCost;

    static readonly int[] DX = { 1, -1, 0, 0, 1, 1, -1, -1 };
    static readonly int[] DZ = { 0, 0, 1, -1, 1, -1, 1, -1 };

    void Start() { if (!baked) Bake(); }

    public void Bake()
    {
        int n = width * depth;
        walkable = new bool[n];
        gCost = new float[n];
        fCost = new float[n];
        parent = new int[n];
        heapIndex = new int[n];
        stamp = new int[n];

        float half = (checkTop - checkBottom) * 0.5f;
        Vector3 ext = new Vector3(agentRadius, half, agentRadius);
        var buffer = new Collider[16];

        for (int z = 0; z < depth; z++)
        {
            for (int x = 0; x < width; x++)
            {
                Vector3 c = CellCenter(x, z);
                bool ok = Physics.Raycast(c + Vector3.up * 0.5f, Vector3.down, 1.2f, ~0, QueryTriggerInteraction.Ignore);
                if (ok)
                {
                    int count = Physics.OverlapBoxNonAlloc(c + Vector3.up * (checkBottom + half), ext, buffer, Quaternion.identity, ~0, QueryTriggerInteraction.Ignore);
                    for (int i = 0; i < count; i++)
                    {
                        var col = buffer[i];
                        if (col.GetComponentInParent<Door>() != null) continue;
                        if (col.GetComponentInParent<PlayerController>() != null) continue;
                        if (col.GetComponentInParent<MonsterAI>() != null) continue;
                        ok = false;
                        break;
                    }
                }
                walkable[z * width + x] = ok;
            }
        }
        baked = true;
    }

    public Vector3 CellCenter(int x, int z) => origin + new Vector3(x * cellSize, 0f, z * cellSize);

    public bool WorldToCell(Vector3 p, out int x, out int z)
    {
        x = Mathf.RoundToInt((p.x - origin.x) / cellSize);
        z = Mathf.RoundToInt((p.z - origin.z) / cellSize);
        return x >= 0 && z >= 0 && x < width && z < depth;
    }

    public bool IsWalkable(int x, int z) => x >= 0 && z >= 0 && x < width && z < depth && walkable[z * width + x];

    public bool IsWalkable(Vector3 p) => WorldToCell(p, out int x, out int z) && IsWalkable(x, z);

    bool NearestWalkable(Vector3 p, out int bx, out int bz)
    {
        WorldToCell(p, out int cx, out int cz);
        bx = cx; bz = cz;
        if (IsWalkable(cx, cz)) return true;
        for (int r = 1; r <= 8; r++)
        {
            float best = float.MaxValue;
            bool found = false;
            for (int dz = -r; dz <= r; dz++)
            for (int dx = -r; dx <= r; dx++)
            {
                if (Mathf.Abs(dx) != r && Mathf.Abs(dz) != r) continue;
                int x = cx + dx, z = cz + dz;
                if (!IsWalkable(x, z)) continue;
                float d = (CellCenter(x, z) - p).sqrMagnitude;
                if (d < best) { best = d; bx = x; bz = z; found = true; }
            }
            if (found) return true;
        }
        return false;
    }

    public Vector3 RandomWalkableNear(Vector3 center, float radius)
    {
        for (int i = 0; i < 30; i++)
        {
            Vector2 r = Random.insideUnitCircle * radius;
            Vector3 p = center + new Vector3(r.x, 0f, r.y);
            if (IsWalkable(p)) { WorldToCell(p, out int x, out int z); return CellCenter(x, z); }
        }
        return center;
    }

    /// <summary>Путь из from в to. Возвращает false, если пути нет.</summary>
    public bool FindPath(Vector3 from, Vector3 to, List<Vector3> result)
    {
        result.Clear();
        if (!baked) Bake();
        if (!NearestWalkable(from, out int sx, out int sz)) return false;
        if (!NearestWalkable(to, out int tx, out int tz)) return false;

        int start = sz * width + sx;
        int goal = tz * width + tx;
        searchId++;
        openHeap.Clear();

        Touch(start);
        gCost[start] = 0f;
        fCost[start] = Heuristic(sx, sz, tx, tz);
        parent[start] = -1;
        HeapPush(start);

        int iterations = 0;
        bool found = false;
        while (openHeap.Count > 0 && iterations++ < 20000)
        {
            int cur = HeapPop();
            if (cur == goal) { found = true; break; }
            heapIndex[cur] = -2; // закрыт
            int cx = cur % width, cz = cur / width;
            for (int d = 0; d < 8; d++)
            {
                int nx = cx + DX[d], nz = cz + DZ[d];
                if (!IsWalkable(nx, nz)) continue;
                if (d >= 4 && (!IsWalkable(cx + DX[d], cz) || !IsWalkable(cx, cz + DZ[d]))) continue; // не режем углы
                int ni = nz * width + nx;
                Touch(ni);
                if (heapIndex[ni] == -2) continue;
                float g = gCost[cur] + (d >= 4 ? 1.4142f : 1f);
                if (heapIndex[ni] >= 0 && g >= gCost[ni]) continue;
                gCost[ni] = g;
                fCost[ni] = g + Heuristic(nx, nz, tx, tz);
                parent[ni] = cur;
                if (heapIndex[ni] >= 0) HeapUp(heapIndex[ni]); else HeapPush(ni);
            }
        }
        if (!found) return false;

        var raw = new List<Vector3>();
        for (int i = goal; i != -1; i = parent[i]) raw.Add(CellCenter(i % width, i / width));
        raw.Reverse();

        // сглаживание: выкидываем промежуточные точки, если по прямой проходимо
        int anchor = 0;
        result.Add(raw[0]);
        for (int i = 2; i < raw.Count; i++)
        {
            if (!ClearLine(raw[anchor], raw[i]))
            {
                anchor = i - 1;
                result.Add(raw[anchor]);
            }
        }
        if (raw.Count > 1) result.Add(raw[raw.Count - 1]);
        return true;
    }

    public bool ClearLine(Vector3 a, Vector3 b)
    {
        float len = Vector3.Distance(a, b);
        int steps = Mathf.CeilToInt(len / (cellSize * 0.5f));
        Vector3 side = Vector3.Cross(Vector3.up, (b - a).normalized) * (agentRadius * 0.9f);
        for (int i = 0; i <= steps; i++)
        {
            Vector3 p = Vector3.Lerp(a, b, i / (float)Mathf.Max(1, steps));
            if (!IsWalkable(p) || !IsWalkable(p + side) || !IsWalkable(p - side)) return false;
        }
        return true;
    }

    float Heuristic(int ax, int az, int bx, int bz)
    {
        int dx = Mathf.Abs(ax - bx), dz = Mathf.Abs(az - bz);
        return (dx + dz) + (1.4142f - 2f) * Mathf.Min(dx, dz);
    }

    void Touch(int i)
    {
        if (stamp[i] == searchId) return;
        stamp[i] = searchId;
        heapIndex[i] = -1;
        gCost[i] = float.MaxValue;
    }

    // --- бинарная куча по fCost
    void HeapPush(int node)
    {
        openHeap.Add(node);
        heapIndex[node] = openHeap.Count - 1;
        HeapUp(openHeap.Count - 1);
    }

    int HeapPop()
    {
        int top = openHeap[0];
        int last = openHeap[openHeap.Count - 1];
        openHeap.RemoveAt(openHeap.Count - 1);
        if (openHeap.Count > 0)
        {
            openHeap[0] = last;
            heapIndex[last] = 0;
            HeapDown(0);
        }
        heapIndex[top] = -1;
        return top;
    }

    void HeapUp(int i)
    {
        while (i > 0)
        {
            int p = (i - 1) / 2;
            if (fCost[openHeap[p]] <= fCost[openHeap[i]]) break;
            Swap(i, p);
            i = p;
        }
    }

    void HeapDown(int i)
    {
        int n = openHeap.Count;
        while (true)
        {
            int l = i * 2 + 1, r = l + 1, m = i;
            if (l < n && fCost[openHeap[l]] < fCost[openHeap[m]]) m = l;
            if (r < n && fCost[openHeap[r]] < fCost[openHeap[m]]) m = r;
            if (m == i) break;
            Swap(i, m);
            i = m;
        }
    }

    void Swap(int a, int b)
    {
        int t = openHeap[a];
        openHeap[a] = openHeap[b];
        openHeap[b] = t;
        heapIndex[openHeap[a]] = a;
        heapIndex[openHeap[b]] = b;
    }

    void OnDrawGizmosSelected()
    {
        if (!drawGizmos) return;
        Gizmos.color = new Color(0.2f, 0.8f, 1f, 0.25f);
        Vector3 size = new Vector3(width * cellSize, 0.05f, depth * cellSize);
        Gizmos.DrawWireCube(origin + new Vector3((width - 1) * cellSize * 0.5f, 0f, (depth - 1) * cellSize * 0.5f), size);
        if (walkable == null) return;
        for (int z = 0; z < depth; z++)
        for (int x = 0; x < width; x++)
        {
            if (!walkable[z * width + x]) continue;
            Gizmos.DrawCube(CellCenter(x, z) + Vector3.up * 0.02f, new Vector3(cellSize * 0.8f, 0.01f, cellSize * 0.8f));
        }
    }
}
