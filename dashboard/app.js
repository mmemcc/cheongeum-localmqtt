// const WS_URL = "ws://localhost:8765";
// const socket = new WebSocket(WS_URL);

const WS_URL = `ws://${window.location.hostname}:8765`;
const socket = new WebSocket(WS_URL);

const MAX_ACCEL_POINTS = 1600;
let timeSortedAccelBuffer = [];
let accelQueue = [];
let isHolding = false;

const holdButton = document.getElementById("hold-btn");

// 릴레이 상태 기록용
const relayStatusMap = {
  relay1: { connection: 0, state: 0, lastChangeUs: null },
  relay2: { connection: 0, state: 0, lastChangeUs: null },
  relay3: { connection: 0, state: 0, lastChangeUs: null },
  relay4: { connection: 0, state: 0, lastChangeUs: null },
};


function updateRelayCards(currentUs) {
  Object.keys(relayStatusMap).forEach((key) => {
    const card = document.getElementById(`${key}-card`);
    const { connection, state, lastChangeUs } = relayStatusMap[key];

    card.querySelector(".relay-connection").textContent = connection ? "Connected" : "Disconnected";
    card.querySelector(".relay-state").textContent = state ? "ON" : "OFF";

    if (lastChangeUs !== null && typeof currentUs === "number") {
      const deltaMs = currentUs - lastChangeUs;
      const minutes = Math.floor(deltaMs / 60000);
      const seconds = Math.floor((deltaMs % 60000) / 1000);
      const formatted = `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
      card.querySelector(".relay-time").textContent = formatted;
    } else {
      card.querySelector(".relay-time").textContent = "-";
    }

    // 스타일 초기화
    card.classList.remove("relay-off", "relay-on", "relay-disconnected");

    if (!connection) {
      card.classList.add("relay-disconnected"); // 회색
    } else if (state) {
      card.classList.add("relay-on"); // 빨강 (ON)
    } else {
      card.classList.add("relay-off"); // 초록 (OFF)
    }
  });
}

holdButton.addEventListener("click", () => {
  isHolding = !isHolding;
  holdButton.textContent = isHolding ? "Resume" : "Hold";
  console.log(isHolding ? "Data update paused" : "Data update resumed");
});

const accplot = new uPlot({
  // title: "Accelerometer (m/s²)",
  width: 700,
  height: 300,
  scales: {
    x: { time: false },
    y: { min: -1, max: 1 }
  },
  axes: [
    { show: false },
    {
      show: true,
    }
  ],
  series: [
    {},
    { label: "X", stroke: "rgb(92, 223, 87)", width: 1.5 },
    { label: "Y", stroke: "rgb(221, 105, 134)", width: 1.5 },
    { label: "Z", stroke: "rgb(86, 120, 214)", width: 1.5 }
  ]
}, [
  Array.from({ length: MAX_ACCEL_POINTS }, (_, i) => i),
  Array(MAX_ACCEL_POINTS).fill(0),
  Array(MAX_ACCEL_POINTS).fill(0),
  Array(MAX_ACCEL_POINTS).fill(0)
], document.getElementById("accel-chart"));

const tempChart = new uPlot({
  // title: "Temperature (°C)",
  width: 600,
  height: 320,
  scales: {
    x: { time: false},
    y: { min: 0, max: 100 }
  },
  axes: [
    {
      label: "시간",
      values: (u, ticks) => ticks.map(t => {
        const totalSec = Math.floor(t / 1000);
        const minutes = Math.floor(totalSec / 60) % 60;
        const seconds = totalSec % 60;
        return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
      })
    },
    {}
  ],
  series: [
    {},
    { label: "압축기-응축기", stroke: "red", width: 1.5 },
    { label: "응축기-드라이어", stroke: "orange", width: 1.5 },
    { label: "드라이어-모세관", stroke: "brown", width: 1.5 },
    { label: "모세관-증발기", stroke: "purple", width: 1.5 },
    { label: "증발기-압축기", stroke: "blue", width: 1.5 },
    { label: "외기온도", stroke: "green", width: 1.5 }
  ]
}, [[], [], [], [], [], [], []], document.getElementById("temp-chart"));

const currentChart = new uPlot({
  width: 600,
  height: 300,
  scales: {
    x: { time: false },
    y: { min: 0, max: 100 }
  },
  axes: [
    {
      label: "시간",
      values: (u, ticks) => ticks.map(t => {
        const totalSec = Math.floor(t / 1000);
        const minutes = Math.floor(totalSec / 60) % 60;
        const seconds = totalSec % 60;
        return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
      })
    },
    {}
  ],
  series: [
    {},
    { label: "압축기", stroke: "red", width: 1.5 },
    { label: "팬", stroke: "orange", width: 1.5 },
    { label: "제상히터", stroke: "brown", width: 1.5 }
  ]
}, [[], [], [], []], document.getElementById("current-chart"));

const humiChart = new uPlot({
  width: 400,
  height: 130,
  scales: {
    x: { time: false },
    y: { min: 0, max: 100 }
  },
  axes: [
    {
      label: "시간",
      values: (u, ticks) => ticks.map(t => {
        const totalSec = Math.floor(t / 1000);
        const minutes = Math.floor(totalSec / 60) % 60;
        const seconds = totalSec % 60;
        return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
      })
    },
    {}
  ],
  series: [
    {},
    { label: "습도", stroke: "blue", width: 1.5 }
  ]
}, [[], []], document.getElementById("humi-chart"));

const in_tempChart = new uPlot({
  width: 400,
  height: 130,
  scales: {
    x: { time: false },
    y: { min: 0, max: 100 }
  },
  axes: [
    {
      label: "시간",
      values: (u, ticks) => ticks.map(t => {
        const totalSec = Math.floor(t / 1000);
        const minutes = Math.floor(totalSec / 60) % 60;
        const seconds = totalSec % 60;
        return `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
      })
    },
    {}
  ],
  series: [
    {},
    { label: "온도", stroke: "red", width: 1.5 }
  ]
}, [[], []], document.getElementById("in-temp-chart"));


function updateAccelPlot(newData) {
  if (timeSortedAccelBuffer.length >= MAX_ACCEL_POINTS) {
    timeSortedAccelBuffer.shift();
  }
  timeSortedAccelBuffer.push(newData);

  const now = Date.now(); // ms 단위
  const xData = Array.from({ length: timeSortedAccelBuffer.length }, (_, i) =>
    now - (timeSortedAccelBuffer.length - 1 - i) * 1000
  );
  // const yX = timeSortedAccelBuffer.map(d => d.x);
  // const yY = timeSortedAccelBuffer.map(d => d.y);
  // const yZ = timeSortedAccelBuffer.map(d => d.z);
  const yX = timeSortedAccelBuffer.map(d => (d.x-16384.0)/ 16384.0 * 9.80665);
  const yY = timeSortedAccelBuffer.map(d => d.y/ 16384.0 * 9.80665);
  const yZ = timeSortedAccelBuffer.map(d => d.z/ 16384.0 * 9.80665);

  accplot.setData([xData, yX, yY, yZ]);
}

function updateAccelTable() {
  const tableBody = document.getElementById("accel-table-body");
  const latest = timeSortedAccelBuffer.slice().reverse().slice(0, 20);
  tableBody.innerHTML = "";
  latest.forEach((d, i) => {
    const prev = latest[i + 1];
    const deltaUs = prev ? d.us - prev.us : "-";
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${d.us}</td>
      <td>${((d.x-16384.0)/ 16384.0 * 9.80665).toFixed(3)}</td>
      <td>${(d.y/ 16384.0 * 9.80665).toFixed(3)}</td>
      <td>${(d.z/ 16384.0 * 9.80665).toFixed(3)}</td>
      <td>${deltaUs}</td>
    `;
    tableBody.appendChild(row);
  });
}

socket.onopen = () => {
  console.log("WebSocket connection established");
};

setInterval(() => {
  if (!isHolding && accelQueue.length > 0) {
    const next = accelQueue.shift();
    updateAccelPlot(next);
    updateAccelTable();
  }
}, 20);

socket.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.accel && Array.isArray(data.accel.accel_data)) {
    const accelChunk = data.accel.accel_data;
    accelChunk.sort((a, b) => a.us - b.us);
    accelQueue.push(...accelChunk);
  }

  if (data.env && data.env.temp_data) {
    const temp_data = data.env.temp_data;
    const currrent_data = data.env.current_data;
    console.log(data.env.current_data);
    console.log(currrent_data);
    const currentTime = Date.now();

    const temp1 = temp_data.temp1;
    const temp2 = temp_data.temp2;
    const temp3 = temp_data.temp3;
    const temp4 = temp_data.temp4;
    const temp5 = temp_data.temp5;
    const temp6 = temp_data.temp6;
    const current1 = currrent_data.current1;
    const current2 = currrent_data.current2;

    if (isHolding) return; // Hold 시 업데이트 중지

    tempChart.setData([
      [...tempChart.data[0], currentTime],
      [...tempChart.data[1], temp1],
      [...tempChart.data[2], temp2],
      [...tempChart.data[3], temp3],
      [...tempChart.data[4], temp4],
      [...tempChart.data[5], temp5],
      [...tempChart.data[6], temp6]
    ]);

    if (tempChart.data[0].length > 300) {
      for (let i = 0; i < 7; i++) {
        tempChart.data[i].shift();
      }
    }

    currentChart.setData([
      [...currentChart.data[0], currentTime],
      [...currentChart.data[1], current1],
      [...currentChart.data[2], current2],
      [...currentChart.data[3], 0]
    ]);

    if (currentChart.data[0].length > 300) {
      for (let i = 0; i < 4; i++) {
        currentChart.data[i].shift();
      }
    }

    
  }

  // 🔄 릴레이 데이터 파싱 처리
  const relayRoot = data.relay?.relay_data;
  const relay_us = relayRoot?.us;

  if (relayRoot && typeof relay_us === "number") {
    ["relay1", "relay2", "relay3", "relay4"].forEach((key) => {
      const value = relayRoot[key];
      if (!Array.isArray(value) || value.length < 2) return;

      const [connection, state] = value;
      const prev = relayStatusMap[key];

      if (prev.state !== state || prev.connection !== connection) {
        relayStatusMap[key] = {
          connection,
          state,
          lastChangeUs: Date.now(),
        };
      }
    });

    updateRelayCards(Date.now());
  }

};