import csv
import json


rows = list(
    csv.DictReader(
        open("tjs_geo.csv", encoding="utf-8")
    )
)

markers = json.dumps(
    rows,
    ensure_ascii=False
)

parts = []

parts.append(
    '<html><head><meta charset="utf-8"><title>TJS GEO Map</title>'
)

parts.append(
    '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
)

parts.append(
    '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">'
)

parts.append(
    '<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>'
)

parts.append(
r'''
<style>

body {
    margin: 0;
    font-family: sans-serif;
}

.bar {
    padding: 12px;
    background: #f7f3ea;
}

.search-box {
    display: flex;
    gap: 7px;
    margin-top: 10px;
}

#satSearch {
    flex: 1;
    min-width: 0;
    padding: 10px;
    font-size: 16px;
    border: 1px solid #999;
    border-radius: 8px;
}

#searchButton {
    padding: 10px 15px;
    border: 0;
    border-radius: 8px;
    background: #2378d3;
    color: white;
    font-weight: bold;
    font-size: 15px;
}

#searchResult {
    min-height: 20px;
    margin-top: 6px;
    font-size: 13px;
}


/* 地図を少し広く */
#map {
    height: 82vh;
    width: 100%;
}


/* ==========================================
   衛星詳細ポップアップ

   ポップアップ自体を巨大化させず、
   中身だけ指でスクロールする
   ========================================== */

.leaflet-popup {
    max-width: 92vw;
}

.leaflet-popup-content-wrapper {
    max-width: 420px;
}

.leaflet-popup-content {
    max-height: 300px;
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
    overscroll-behavior: contain;
    margin: 12px 18px;
}


/* スクロールバーを少し細く */
.leaflet-popup-content::-webkit-scrollbar {
    width: 5px;
}

.leaflet-popup-content::-webkit-scrollbar-thumb {
    background: #999;
    border-radius: 5px;
}

</style>

</head>

<body>
'''
)

parts.append(
    f'''
<div class="bar">

    <b>TJS GEO Map</b><br>

    CelesTrak GEO + GPZから抽出したTJSの地図表示<br>

    表示衛星数：{len(rows)} 機

    <div class="search-box">

        <input
            id="satSearch"
            type="text"
            placeholder="衛星名 または NORAD ID"
            autocomplete="off"
        >

        <button id="searchButton">
            🔍 検索
        </button>

    </div>

    <div id="searchResult"></div>

</div>
'''
)

parts.append(
    '<div id="map"></div>'
)

parts.append(
    '<script>'
)

parts.append(
    'const data = ' + markers + ';'
)

parts.append(
r'''

const map =
    L.map("map").setView(
        [0, 140],
        2
    );


L.tileLayer(
    "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    {
        maxZoom: 6,
        attribution: "OpenStreetMap"
    }
).addTo(map);



/* =========================================================
   打上げ場所
   ========================================================= */

const LAUNCH_SITES = {

    // 中国
    "WSC": "文昌衛星発射場",
    "XICLF": "西昌衛星発射センター",
    "JSC": "酒泉衛星発射センター",
    "TAISC": "太原衛星発射センター",
    "SCSLA": "南シナ海打上げ区域",
    "YSLA": "黄海打上げ区域",

    // ロシア・旧ソ連圏
    "DLS": "ドンバロフスキー発射場",
    "PLMSC": "プレセツク宇宙基地",
    "KYMSC": "カプースチン・ヤール",
    "VOSTO": "ボストーチヌイ宇宙基地",
    "SVOBO": "スヴォボードヌイ宇宙基地",
    "TYMSC": "バイコヌール宇宙基地",

    // その他
    "SEAL": "シーローンチ海上発射施設",
    "SUBL": "潜水艦発射",
    "UNK": "不明"
};



function launchSiteName(code) {

    if (!code) {
        return "不明";
    }

    const key =
        String(code)
            .trim()
            .toUpperCase();

    const name =
        LAUNCH_SITES[key];

    if (name) {

        return (
            name +
            "（" +
            key +
            "）"
        );
    }

    return key;
}



/* =========================================================
   衛星カテゴリ
   ========================================================= */

function catOf(r) {

    const n =
        String(
            r.name || ""
        ).toUpperCase();

    const lat =
        Math.abs(
            parseFloat(
                r.lat || "0"
            )
        );


    if (lat > 3) {

        return [
            "#dd6b20",
            "移動中・傾斜大",
            "GEO付近だが南北に大きく振れている。移動中・静止化途中・傾斜軌道の可能性"
        ];
    }


    if (
        n.includes("TJS") ||
        n.includes("TONGXIN")
    ) {

        return [
            "#2b6cb0",
            "TJS・通信技術試験",
            "中国の通信技術試験衛星系。GEO上の位置と移動を継続監視"
        ];
    }


    return [
        "#718096",
        "未整理",
        "用途未整理。公開情報または自分メモで追記"
    ];
}



/* =========================================================
   打上げ情報
   ========================================================= */

function formatLaunchDate(date) {

    if (!date) {
        return "不明";
    }

    return date.replaceAll(
        "-",
        "/"
    );
}



function launchAgeOf(date) {

    if (!date) {
        return "不明";
    }

    const launch =
        new Date(
            date +
            "T00:00:00Z"
        );


    if (
        Number.isNaN(
            launch.getTime()
        )
    ) {
        return "不明";
    }


    const diff =
        Date.now() -
        launch.getTime();


    if (diff < 0) {
        return "未打上げ";
    }


    const days =
        Math.floor(
            diff / 86400000
        );


    if (days < 365) {
        return days + "日";
    }


    const years =
        Math.floor(
            days / 365.2425
        );


    const remainDays =
        Math.floor(
            days -
            years * 365.2425
        );


    return (
        years +
        "年 " +
        remainDays +
        "日"
    );
}



/* =========================================================
   TLE経過時間
   ========================================================= */

function ageOf(epochIso) {

    const epoch =
        new Date(
            epochIso
        );


    if (
        Number.isNaN(
            epoch.getTime()
        )
    ) {
        return "不明";
    }


    let diff =
        Date.now() -
        epoch.getTime();


    const future =
        diff < 0;


    diff =
        Math.abs(diff);


    const totalMinutes =
        Math.floor(
            diff / 60000
        );


    const days =
        Math.floor(
            totalMinutes / 1440
        );


    const hours =
        Math.floor(
            (totalMinutes % 1440) / 60
        );


    const minutes =
        totalMinutes % 60;


    let text = "";


    if (days > 0) {

        text +=
            days +
            "日 ";
    }


    text +=
        hours +
        "時間" +
        minutes +
        "分";


    return future
        ? "未来 " + text
        : text;
}



/* =========================================================
   TLE鮮度
   ========================================================= */

function freshnessOf(epochIso) {

    const epoch =
        new Date(
            epochIso
        );


    if (
        Number.isNaN(
            epoch.getTime()
        )
    ) {

        return {
            color: "#718096",
            icon: "⚪",
            text: "不明"
        };
    }


    const ageHours =
        (
            Date.now() -
            epoch.getTime()
        ) / 3600000;


    if (ageHours < 24) {

        return {
            color: "#16a34a",
            icon: "🟢",
            text: "新鮮"
        };
    }


    if (ageHours < 72) {

        return {
            color: "#ca8a04",
            icon: "🟡",
            text: "やや古い"
        };
    }


    if (ageHours < 168) {

        return {
            color: "#ea580c",
            icon: "🟠",
            text: "古い"
        };
    }


    return {
        color: "#dc2626",
        icon: "🔴",
        text: "要注意"
    };
}



/* =========================================================
   ポップアップ
   ========================================================= */

function popOf(r) {

    const c =
        catOf(r);


    const fresh =
        freshnessOf(
            r.epoch_iso
        );


    return (

        "<b>" +
        r.name +
        "</b><br>" +


        "<span style='" +

        "display:inline-block;" +
        "margin:4px 0;" +
        "padding:2px 8px;" +
        "border-radius:10px;" +

        "background:" +
        c[0] +
        ";" +

        "color:white;" +
        "font-size:12px;" +

        "'>" +

        c[1] +

        "</span><br>" +


        "<b>NORAD ID：</b>" +
        r.norad +
        "<br>" +


        "<b>緯度：</b>" +
        r.lat +
        "°<br>" +


        "<b>経度：</b>" +
        r.lon +
        "°<br>" +


        "<b>高度：</b>" +
        r.alt_km +
        " km<br>" +


        "<hr>" +


        "🚀 <b>打上げ日：</b>" +

        formatLaunchDate(
            r.launch_date
        ) +

        "<br>" +


        "📍 <b>打上げ場所：</b>" +

        launchSiteName(
            r.launch_site
        ) +

        "<br>" +


        "🛰 <b>打上げから：</b>" +

        launchAgeOf(
            r.launch_date
        ) +

        "<br>" +


        "<hr>" +


        "<b>TLEエポック：</b>" +
        r.epoch_day +
        "<br>" +


        "<b>エポック日時：</b>" +
        r.epoch_utc +
        "<br>" +


        "<b>経過時間：</b>" +

        ageOf(
            r.epoch_iso
        ) +

        "<br>" +


        "<b>TLE鮮度：</b>" +


        "<span style='" +

        "font-weight:bold;" +

        "color:" +
        fresh.color +
        ";" +

        "'>" +


        fresh.icon +
        " " +
        fresh.text +


        "</span><br>" +


        "<hr>" +


        "<b>分類：</b>" +
        c[1] +
        "<br>" +


        "<b>任務メモ：</b>" +
        c[2]
    );
}



/* =========================================================
   マーカー
   ========================================================= */

const satelliteMarkers = [];


data.forEach(r => {

    const c =
        catOf(r);


    const marker =
        L.circleMarker(

            [
                parseFloat(
                    r.lat
                ),

                parseFloat(
                    r.lon
                )
            ],

            {
                radius: 8,
                color: "#1a202c",
                weight: 1,
                fillColor: c[0],
                fillOpacity: 0.9
            }
        )

        .addTo(map)

        .bindPopup(
            popOf(r),
            {
                maxWidth: 420
            }
        );


    satelliteMarkers.push({

        data: r,
        marker: marker
    });
});



/* =========================================================
   検索用文字列正規化

   TJS-12
   TJS12
   Tjs12
   TJS 12

   全部同じ扱い
   ========================================================= */

function normalizeSearch(value) {

    return String(
        value || ""
    )

    .toUpperCase()

    .replace(
        /[^A-Z0-9]/g,
        ""
    );
}



/* =========================================================
   衛星検索
   ========================================================= */

function searchSatellite() {

    const input =
        document.getElementById(
            "satSearch"
        );


    const result =
        document.getElementById(
            "searchResult"
        );


    const query =
        normalizeSearch(
            input.value.trim()
        );


    if (!query) {

        result.textContent =
            "衛星名かNORAD IDを入力してください";

        return;
    }


    let found =
        satelliteMarkers.find(
            item => {

                const name =
                    normalizeSearch(
                        item.data.name
                    );

                const norad =
                    normalizeSearch(
                        item.data.norad
                    );

                return (
                    name === query ||
                    norad === query
                );
            }
        );


    if (!found) {

        found =
            satelliteMarkers.find(
                item => {

                    const name =
                        normalizeSearch(
                            item.data.name
                        );

                    const norad =
                        normalizeSearch(
                            item.data.norad
                        );

                    return (
                        name.includes(query) ||
                        norad.includes(query)
                    );
                }
            );
    }


    if (!found) {

        result.textContent =
            "❌ 該当する衛星がありません";

        return;
    }


    const r =
        found.data;


    const marker =
        found.marker;


    map.setView(

        [
            parseFloat(
                r.lat
            ),

            parseFloat(
                r.lon
            )
        ],

        5,

        {
            animate: true
        }
    );


    marker.openPopup();


    marker.setRadius(
        14
    );


    setTimeout(

        function() {

            marker.setRadius(
                8
            );
        },

        2500
    );


    result.textContent =
        "✅ " +
        r.name +
        " / NORAD " +
        r.norad;
}



/* =========================================================
   検索ボタン
   ========================================================= */

document
    .getElementById(
        "searchButton"
    )
    .addEventListener(

        "click",

        searchSatellite
    );



/* =========================================================
   Enterでも検索
   ========================================================= */

document
    .getElementById(
        "satSearch"
    )
    .addEventListener(

        "keydown",

        function(event) {

            if (
                event.key ===
                "Enter"
            ) {

                event.preventDefault();

                searchSatellite();
            }
        }
    );



/* =========================================================
   衛星カテゴリ
   ========================================================= */

const legend =
    L.control({
        position:
            "bottomleft"
    });



legend.onAdd =
    function() {

        const div =
            L.DomUtil.create(
                "div",
                "info legend"
            );


        div.id =
            "satLegend";


        div.style.background =
            "white";

        div.style.padding =
            "10px";

        div.style.borderRadius =
            "8px";

        div.style.boxShadow =
            "0 1px 5px rgba(0,0,0,0.3)";

        div.style.fontSize =
            "13px";


        div.innerHTML =

            "<b>衛星カテゴリ</b><br>" +

            "<div>🔵 TJS・通信技術試験</div>" +

            "<div>🟠 移動中・傾斜大</div>" +

            "<div>⚫ 未整理</div>";


        return div;
    };


legend.addTo(map);



/* =========================================================
   詳細を開いている間はカテゴリを隠す
   ========================================================= */

map.on(
    "popupopen",

    function() {

        const legendBox =
            document.getElementById(
                "satLegend"
            );


        if (legendBox) {

            legendBox.style.display =
                "none";
        }
    }
);



/* =========================================================
   詳細を閉じたらカテゴリ復活
   ========================================================= */

map.on(
    "popupclose",

    function() {

        const legendBox =
            document.getElementById(
                "satLegend"
            );


        if (legendBox) {

            legendBox.style.display =
                "block";
        }
    }
);

'''
)

parts.append(
    '</script></body></html>'
)


open(
    "tjs_map.html",
    "w",
    encoding="utf-8"
).write(
    "\n".join(parts)
)


print(
    "saved tjs_map.html"
)

print(
    f"count: {len(rows)}"
)