const socket = new WebSocket("ws://localhost:8765");

let chart;
let dataBuffer = {
  time: [],
  x: [],
  y: [],
  z: [],
};

const MAX_POINTS = 1600; // 1초치

function initChart() {
  const opts = {
    width: 800,
    height: 400,
    title: "Accelerometer (x, y, z)",
    scales: {
      x: { time: false },
    },
    series: [
      {},
      { label: "x", stroke: "red" },
      { label: "y", stroke: "green" },
      { label: "z", stroke: "blue" },
    ],
  };

  const uplotData = [
    dataBuffer.time,
    dataBuffer.x,
    dataBuffer.y,
    dataBuffer.z,
  ];

  chart = new uPlot(opts, uplotData, document.getElementById("chart"));
}

function updateChart() {
  chart.setData([
    dataBuffer.time,
    dataBuffer.x,
    dataBuffer.y,
    dataBuffer.z,
  ]);
}

socket.onmessage = (event) => {
  try {
    const json = JSON.parse(event.data);

    if (!Array.isArray(json.accel_data)) return;

    const now = Date.now();
    json.accel_data.forEach((point, idx) => {
      dataBuffer.time.push(now + idx); // or idx only
      dataBuffer.x.push(point.x);
      dataBuffer.y.push(point.y);
      dataBuffer.z.push(point.z);
    });

    // Trim old data
    if (dataBuffer.time.length > MAX_POINTS) {
      dataBuffer.time = dataBuffer.time.slice(-MAX_POINTS);
      dataBuffer.x = dataBuffer.x.slice(-MAX_POINTS);
      dataBuffer.y = dataBuffer.y.slice(-MAX_POINTS);
      dataBuffer.z = dataBuffer.z.slice(-MAX_POINTS);
    }

    updateChart();
  } catch (err) {
    console.error("데이터 처리 중 에러:", err);
  }
};

socket.onopen = () => {
  console.log("WebSocket 연결됨");
};

initChart();
