Shader "Hidden/HorrorPostFX"
{
    Properties
    {
        _MainTex ("Source", 2D) = "white" {}
    }
    SubShader
    {
        Cull Off ZWrite Off ZTest Always

        Pass
        {
            CGPROGRAM
            #pragma vertex vert_img
            #pragma fragment frag
            #include "UnityCG.cginc"

            sampler2D _MainTex;
            float _Vignette, _Grain, _Chroma, _Saturation, _Contrast, _Scan, _Fear, _Flash;
            float4 _Tint;

            float hash(float2 p)
            {
                return frac(sin(dot(p, float2(12.9898, 78.233))) * 43758.5453);
            }

            fixed4 frag (v2f_img i) : SV_Target
            {
                float2 uv = i.uv;
                float2 c = uv - 0.5;
                float t = _Time.y;

                // дрожь картинки от страха + редкие "срывы" строк как у дешёвой камеры
                uv.x += sin(uv.y * 30.0 + t * 4.0) * 0.0018 * _Fear;
                float tear = step(0.995 - _Fear * 0.02, hash(float2(floor(uv.y * 60.0), floor(t * 12.0))));
                uv.x += tear * 0.01 * (hash(float2(t, uv.y)) - 0.5);

                float ca = _Chroma * (1.0 + _Fear * 3.0 + _Flash * 5.0);
                float2 dir = c * ca * 2.0;
                float3 col;
                col.r = tex2D(_MainTex, uv + dir).r;
                col.g = tex2D(_MainTex, uv).g;
                col.b = tex2D(_MainTex, uv - dir).b;

                float lum = dot(col, float3(0.299, 0.587, 0.114));
                col = lerp(lum.xxx, col, saturate(_Saturation - _Fear * 0.35));
                col = max(0.0, (col - 0.18) * _Contrast + 0.18);
                col *= _Tint.rgb;

                // зерно, сильнее в темноте
                float n = hash(uv * _ScreenParams.xy + frac(t * 37.0)) - 0.5;
                col += n * _Grain * (1.0 + _Fear) * (1.2 - saturate(lum * 2.0));

                // строки развёртки
                col *= 1.0 - _Scan * (0.5 + 0.5 * sin(uv.y * _ScreenParams.y * 1.6));

                // виньетка сжимается при страхе
                float v = 1.0 - dot(c, c) * _Vignette * (2.0 + _Fear * 2.0);
                col *= saturate(v);

                // красная вспышка
                col = lerp(col, float3(lum * 1.8 + 0.12, lum * 0.1, lum * 0.08), saturate(_Flash) * 0.75);

                return fixed4(col, 1.0);
            }
            ENDCG
        }
    }
    Fallback Off
}
