// const baseUrl = "http://127.0.0.1:8000";

// let selectedCities = [];
// let selectedPollutants = [];
// let pollutantMap = {};

// window.onload = function () {
//   loadCities();
//   loadPollutants();

//   // Default time values (no UI change, just default values)
//   const startTime = document.getElementById("startTime");
//   const endTime = document.getElementById("endTime");

//   if (startTime && !startTime.value) startTime.value = "00:00";
//   if (endTime && !endTime.value) endTime.value = "23:59";

//   const citySearch = document.getElementById("citySearch");
//   if (citySearch) {
//     citySearch.addEventListener("input", () =>
//       filterDropdown("citySearch", "cityDropdown")
//     );
//   }

//   const pollutantSearch = document.getElementById("pollutantSearch");
//   if (pollutantSearch) {
//     pollutantSearch.addEventListener("input", () =>
//       filterDropdown("pollutantSearch", "pollutantDropdown")
//     );
//   }

//   const exportBtn = document.getElementById("exportBtn");

//   if (exportBtn) {
//     exportBtn.onclick = handleExport;
//   }
// };

// // -------------------- LOAD CITIES --------------------

// async function loadCities() {
//   const res = await fetch(`${baseUrl}/meta/cities`);
//   const data = await res.json();

//   const formattedCities = data.cities.map(c => ({
//     label: `${c.city} (${c.state})`,
//     value: c.city
//   }));

//   createMultiSelectWithLabel(
//     "cityDropdown",
//     formattedCities,
//     selectedCities,
//     "selectedCities"
//   );
// }


// // 


// // -------------------- LOAD POLLUTANTS --------------------

// async function loadPollutants() {
//   const res = await fetch(`${baseUrl}/meta/pollutants`);
//   const data = await res.json();

//   pollutantMap = data.pollutants;
//   const pollutantNames = Object.keys(pollutantMap);

//   createMultiSelect(
//     "pollutantDropdown",
//     pollutantNames,
//     selectedPollutants,
//     "selectedPollutants"
//   );
// }

// // -------------------- SEARCH FILTER --------------------

// function filterDropdown(searchId, dropdownId) {
//   const input = document.getElementById(searchId);
//   const filter = (input?.value || "").toLowerCase();
//   const dropdown = document.getElementById(dropdownId);
//   if (!dropdown) return;

//   const divs = dropdown.getElementsByTagName("div");

//   for (let i = 0; i < divs.length; i++) {
//     const txtValue = divs[i].textContent || divs[i].innerText;
//     divs[i].style.display = txtValue.toLowerCase().includes(filter)
//       ? ""
//       : "none";
//   }
// }

// // -------------------- MULTI SELECT --------------------

// function createMultiSelect(containerId, items, selectedArray, tagContainerId) {
//   const container = document.getElementById(containerId);
//   const tagContainer = document.getElementById(tagContainerId);
//   if (!container || !tagContainer) return;

//   container.innerHTML = "";

//   items.forEach((item) => {
//     const div = document.createElement("div");
//     div.textContent = item;

//     div.onclick = function () {
//       if (!selectedArray.includes(item)) selectedArray.push(item);
//       renderTags(tagContainer, selectedArray, containerId);
//     };

//     container.appendChild(div);
//   });
// }

// function renderTags(container, selectedArray, type) {
//   container.innerHTML = "";

//   selectedArray.forEach((item, index) => {
//     const tag = document.createElement("div");
//     tag.className = "tag";

//     tag.innerHTML =
//       `<span>${escapeHtml(item)}</span>` +
//       `<button type="button" class="remove-btn" onclick="removeItem('${type}', ${index})">×</button>`;

//     container.appendChild(tag);
//   });
// }

// function escapeHtml(str) {
//   return String(str)
//     .replaceAll("&", "&amp;")
//     .replaceAll("<", "&lt;")
//     .replaceAll(">", "&gt;")
//     .replaceAll('"', "&quot;")
//     .replaceAll("'", "&#039;");
// }

// function removeItem(type, index) {
//   if (type === "cityDropdown") {
//     selectedCities.splice(index, 1);
//     renderTags(document.getElementById("selectedCities"), selectedCities, "cityDropdown");
//   } else {
//     selectedPollutants.splice(index, 1);
//     renderTags(document.getElementById("selectedPollutants"), selectedPollutants, "pollutantDropdown");
//   }
// }

// function createMultiSelectWithLabel(containerId, items, selectedArray, tagContainerId) {
//   const container = document.getElementById(containerId);
//   const tagContainer = document.getElementById(tagContainerId);
//   if (!container || !tagContainer) return;

//   container.innerHTML = "";

//   items.forEach(item => {
//     const div = document.createElement("div");
//     div.textContent = item.label;

//     div.onclick = function () {
//       if (!selectedArray.includes(item.label)) selectedArray.push(item.label);
//       renderTags(tagContainer, selectedArray, containerId);
//     };

//     container.appendChild(div);
//   });
// }


// // -------------------- EXPORT HANDLER --------------------

// // async function handleExport() {
// //   const loader = document.getElementById("loader");
// //   const message = document.getElementById("message");

// //   if (loader) loader.classList.remove("hidden");
// //   if (message) message.innerHTML = "";

// //   try {
// //     const aggregation = document.getElementById("aggregation")?.value;
// //     const startDate = document.getElementById("startDate")?.value;
// //     const startTime = document.getElementById("startTime")?.value;
// //     const endDate = document.getElementById("endDate")?.value;
// //     const endTime = document.getElementById("endTime")?.value;

// //     if (!aggregation) throw new Error("Aggregation not selected.");
// //     if (!startDate || !startTime || !endDate || !endTime)
// //       throw new Error("Please select start and end date & time.");

// //     if (!selectedCities.length)
// //       throw new Error("Please select at least 1 city.");

// //     const backendPollutants = selectedPollutants
// //       .map((name) => pollutantMap[name])
// //       .filter(Boolean);

// //     if (!backendPollutants.length)
// //       throw new Error("Please select at least 1 pollutant.");

// //     const payload = {
// //       start: `${startDate}T${startTime}`,
// //       end: `${endDate}T${endTime}`,
// //       aggregation,
// //       cities: selectedCities,
// //       pollutants: backendPollutants,
// //       gaps: 1,
// //       gap_value: "NULL",
// //     };

// //     const response = await fetch(`${baseUrl}/export`, {
// //       method: "POST",
// //       headers: { "Content-Type": "application/json" },
// //       body: JSON.stringify(payload),
// //     });

// //     if (!response.ok) {
// //       const errorText = await response.text();
// //       throw new Error(errorText);
// //     }

// //     const blob = await response.blob();
// //     const url = window.URL.createObjectURL(blob);

// //     const stamp = new Date().toISOString().replaceAll(":", "-");
// //     const a = document.createElement("a");
// //     a.href = url;
// //     a.download = `city_air_quality_${aggregation}_${stamp}.xlsx`;

// //     document.body.appendChild(a);
// //     a.click();
// //     a.remove();
// //     window.URL.revokeObjectURL(url);

// //     if (message) message.innerHTML = "✅ Export Successful!";
// //   } catch (err) {
// //     if (message) message.innerHTML = "❌ Error: " + err.message;
// //   }

// //   if (loader) loader.classList.add("hidden");
// // }
// // async function handleExport() {

// //   const progressContainer = document.getElementById("progressContainer");
// //   const progressBar = document.getElementById("progressBar");
// //   const message = document.getElementById("message");

// //   progressContainer.style.display = "block";
// //   progressBar.style.width = "0%";

// //   const aggregation = document.getElementById("aggregation").value;
// //   const startDate = document.getElementById("startDate").value;
// //   const startTime = document.getElementById("startTime").value;
// //   const endDate = document.getElementById("endDate").value;
// //   const endTime = document.getElementById("endTime").value;

// //   const payload = {
// //     start: `${startDate}T${startTime}`,
// //     end: `${endDate}T${endTime}`,
// //     aggregation,
// //     cities: selectedCities,
// //     pollutants: selectedPollutants.map(n => pollutantMap[n]),
// //     gaps: 1,
// //     gap_value: "NULL"
// //   };

// //   const response = await fetch(`${baseUrl}/export`, {
// //     method: "POST",
// //     headers: { "Content-Type": "application/json" },
// //     body: JSON.stringify(payload)
// //   });

// //   const result = await response.json();
// //   const jobId = result.job_id;
// //   const filePath = result.file_path;

// //   const interval = setInterval(async () => {
// //     const prog = await fetch(`${baseUrl}/progress/${jobId}`);
// //     const data = await prog.json();

// //     progressBar.style.width = data.progress + "%";

// //     if (data.progress >= 100) {
// //       clearInterval(interval);

// //       const download = await fetch(`${baseUrl}/download?file_path=${encodeURIComponent(filePath)}`);
// //       const blob = await download.blob();
// //       const url = window.URL.createObjectURL(blob);

// //       const a = document.createElement("a");
// //       a.href = url;
// //       a.download = "city_air_quality.xlsx";
// //       a.click();
// //     }
// //   }, 1000);
// // }
// async function handleExport() {

//   const progressContainer = document.getElementById("progressContainer");
//   const progressBar = document.getElementById("progressBar");
//   const progressText = document.getElementById("progressText");
//   const message = document.getElementById("message");

//   progressContainer.style.display = "block";
//   progressBar.style.width = "0%";
//   progressText.innerText = "0%";
//   message.innerHTML = "";

//   const aggregation = document.getElementById("aggregation").value;
//   const startDate = document.getElementById("startDate").value;
//   const startTime = document.getElementById("startTime").value;
//   const endDate = document.getElementById("endDate").value;
//   const endTime = document.getElementById("endTime").value;

//   const payload = {
//     start: `${startDate}T${startTime}`,
//     end: `${endDate}T${endTime}`,
//     aggregation,
//     cities: selectedCities,
//     pollutants: selectedPollutants.map(n => pollutantMap[n]),
//     gaps: 1,
//     gap_value: "NULL"
//   };

//   const response = await fetch(`${baseUrl}/export`, {
//     method: "POST",
//     headers: { "Content-Type": "application/json" },
//     body: JSON.stringify(payload)
//   });

//   const result = await response.json();
//   const jobId = result.job_id;
//   const filePath = result.file_path;

//   const interval = setInterval(async () => {

//     const prog = await fetch(`${baseUrl}/progress/${jobId}`);
//     const data = await prog.json();

//     progressBar.style.width = data.progress + "%";
//     progressText.innerText = data.progress + "%";

//     if (data.progress >= 100) {

//       clearInterval(interval);

//       const download = await fetch(`${baseUrl}/download?file_path=${encodeURIComponent(filePath)}`);
//       const blob = await download.blob();
//       const url = window.URL.createObjectURL(blob);

//       const a = document.createElement("a");
//       a.href = url;
//       a.download = "city_air_quality.xlsx";
//       a.click();

//       message.innerHTML = "✅ Export Completed";

//       setTimeout(() => {
//         progressContainer.style.display = "none";
//       }, 2000);
//     }

//   }, 800);
// }
const baseUrl = "http://127.0.0.1:8000";

let selectedCities = [];
let selectedPollutants = [];
let pollutantMap = {};

window.onload = function () {
  loadCities();
  loadPollutants();

  const startTime = document.getElementById("startTime");
  const endTime = document.getElementById("endTime");

  if (startTime && !startTime.value) startTime.value = "00:00";
  if (endTime && !endTime.value) endTime.value = "23:59";

  const citySearch = document.getElementById("citySearch");
  if (citySearch) {
    citySearch.addEventListener("input", () =>
      filterDropdown("citySearch", "cityDropdown")
    );
  }

  const pollutantSearch = document.getElementById("pollutantSearch");
  if (pollutantSearch) {
    pollutantSearch.addEventListener("input", () =>
      filterDropdown("pollutantSearch", "pollutantDropdown")
    );
  }

  const exportBtn = document.getElementById("exportBtn");
  if (exportBtn) exportBtn.onclick = handleExport;
};



// -------------------- LOAD CITIES --------------------

async function loadCities() {
  const res = await fetch(`${baseUrl}/meta/cities`);
  const data = await res.json();

  const formattedCities = data.cities.map(c => ({
    label: `${c.city} (${c.state})`,
    value: c.city
  }));

  createMultiSelectWithLabel(
    "cityDropdown",
    formattedCities,
    selectedCities,
    "selectedCities"
  );
}



// -------------------- LOAD POLLUTANTS --------------------

async function loadPollutants() {
  const res = await fetch(`${baseUrl}/meta/pollutants`);
  const data = await res.json();

  pollutantMap = data.pollutants;
  const pollutantNames = Object.keys(pollutantMap);

  createMultiSelect(
    "pollutantDropdown",
    pollutantNames,
    selectedPollutants,
    "selectedPollutants"
  );
}



// -------------------- SEARCH FILTER --------------------

function filterDropdown(searchId, dropdownId) {
  const input = document.getElementById(searchId);
  const filter = (input?.value || "").toLowerCase();
  const dropdown = document.getElementById(dropdownId);
  if (!dropdown) return;

  const divs = dropdown.getElementsByTagName("div");

  for (let i = 0; i < divs.length; i++) {
    const txtValue = divs[i].textContent || divs[i].innerText;
    divs[i].style.display = txtValue.toLowerCase().includes(filter)
      ? ""
      : "none";
  }
}



// -------------------- MULTI SELECT --------------------

function createMultiSelect(containerId, items, selectedArray, tagContainerId) {
  const container = document.getElementById(containerId);
  const tagContainer = document.getElementById(tagContainerId);
  if (!container || !tagContainer) return;

  container.innerHTML = "";

  items.forEach((item) => {
    const div = document.createElement("div");
    div.textContent = item;

    div.onclick = function () {
      if (!selectedArray.includes(item)) selectedArray.push(item);
      renderTags(tagContainer, selectedArray, containerId);
    };

    container.appendChild(div);
  });
}

function createMultiSelectWithLabel(containerId, items, selectedArray, tagContainerId) {
  const container = document.getElementById(containerId);
  const tagContainer = document.getElementById(tagContainerId);
  if (!container || !tagContainer) return;

  container.innerHTML = "";

  items.forEach(item => {
    const div = document.createElement("div");
    div.textContent = item.label;

    div.onclick = function () {
      if (!selectedArray.includes(item.label)) selectedArray.push(item.label);
      renderTags(tagContainer, selectedArray, containerId);
    };

    container.appendChild(div);
  });
}

function renderTags(container, selectedArray, type) {
  container.innerHTML = "";

  selectedArray.forEach((item, index) => {
    const tag = document.createElement("div");
    tag.className = "tag";

    tag.innerHTML =
      `<span>${escapeHtml(item)}</span>` +
      `<button type="button" class="remove-btn" onclick="removeItem('${type}', ${index})">×</button>`;

    container.appendChild(tag);
  });
}

function removeItem(type, index) {
  if (type === "cityDropdown") {
    selectedCities.splice(index, 1);
    renderTags(document.getElementById("selectedCities"), selectedCities, "cityDropdown");
  } else {
    selectedPollutants.splice(index, 1);
    renderTags(document.getElementById("selectedPollutants"), selectedPollutants, "pollutantDropdown");
  }
}

function escapeHtml(str) {
  return String(str)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}



// -------------------- EXPORT HANDLER WITH PROGRESS --------------------

async function handleExport() {

  try {

    const progressContainer = document.getElementById("progressContainer");
    const progressBar = document.getElementById("progressBar");
    const progressText = document.getElementById("progressText");
    const message = document.getElementById("message");

    progressContainer.style.display = "block";
    progressBar.style.width = "0%";
    if (progressText) progressText.innerText = "0%";
    message.innerHTML = "";

    const aggregation = document.getElementById("aggregation").value;
    const startDate = document.getElementById("startDate").value;
    const startTime = document.getElementById("startTime").value;
    const endDate = document.getElementById("endDate").value;
    const endTime = document.getElementById("endTime").value;

    const payload = {
      start: `${startDate}T${startTime}`,
      end: `${endDate}T${endTime}`,
      aggregation,
      cities: selectedCities,
      pollutants: selectedPollutants.map(n => pollutantMap[n]),
      gaps: 1,
      gap_value: "NULL"
    };

    const response = await fetch(`${baseUrl}/export`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const result = await response.json();
    const jobId = result.job_id;
    const filePath = result.file_path;

    const interval = setInterval(async () => {

      const prog = await fetch(`${baseUrl}/progress/${jobId}`);
      const data = await prog.json();

      progressBar.style.width = data.progress + "%";
      if (progressText) progressText.innerText = data.progress + "%";

      if (data.progress >= 100) {

        clearInterval(interval);

        const download = await fetch(`${baseUrl}/download?file_path=${encodeURIComponent(filePath)}`);
        const blob = await download.blob();
        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = `city_air_quality_${Date.now()}.xlsx`;
        document.body.appendChild(a);
        a.click();
        a.remove();

        window.URL.revokeObjectURL(url);

        showModal();

        setTimeout(() => {
          closeModal();
        }, 3000);
      }

    }, 1000);

  } catch (err) {
    alert("Error: " + err.message);
  }
}



// -------------------- DOWNLOAD MODAL --------------------

function showModal() {
  const modal = document.getElementById("downloadModal");
  if (modal) modal.style.display = "block";
}

function closeModal() {
  const modal = document.getElementById("downloadModal");
  if (modal) modal.style.display = "none";
}