document.addEventListener("DOMContentLoaded", function () {
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const sidebar = document.getElementById("sidebar");
    const clock = document.getElementById("clock");

    /* ============================= */
    /* MOBILE SIDEBAR */
    /* ============================= */

    if (mobileMenuBtn && sidebar) {
        mobileMenuBtn.addEventListener("click", function () {
            sidebar.classList.toggle("show");
        });
    }

    /* ============================= */
    /* LIVE CLOCK */
    /* ============================= */

    function updateClock() {
        const now = new Date();

        const formattedTime = now.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit"
        });

        const formattedDate = now.toLocaleDateString([], {
            year: "numeric",
            month: "short",
            day: "numeric"
        });

        if (clock) {
            clock.textContent = `${formattedDate} | ${formattedTime}`;
        }
    }

    updateClock();
    setInterval(updateClock, 1000);

    /* ============================= */
    /* DASHBOARD LIVE DATA */
    /* ============================= */

    async function refreshDashboardData() {
        try {
            const response = await fetch("/api/dashboard-data");

            if (!response.ok) {
                return;
            }

            const data = await response.json();

            const totalPatients = document.querySelector("[data-live='total_patients']");
            const totalRecords = document.querySelector("[data-live='total_records']");
            const attentionRecords = document.querySelector("[data-live='attention_records']");
            const documentationReduction = document.querySelector("[data-live='documentation_reduction']");

            if (totalPatients) {
                totalPatients.textContent = data.stats.total_patients;
            }

            if (totalRecords) {
                totalRecords.textContent = data.stats.total_records;
            }

            if (attentionRecords) {
                attentionRecords.textContent = data.stats.attention_records;
            }

            if (documentationReduction) {
                documentationReduction.textContent = data.stats.documentation_reduction + "%";
            }

            // Update Vitals & BMI chart data
            const vitalsCharts = document.querySelectorAll(".vitals-trend-chart-container, #bmiLineChart, #vitalsLineChart");
            vitalsCharts.forEach(function (chart) {
                const updatedRecords = data.vitals_chart_records || data.bmi_chart_records;
                if (updatedRecords) {
                    chart.setAttribute("data-records", JSON.stringify(updatedRecords));
                    chart.dispatchEvent(new Event("recordsUpdated"));
                }
            });

            // Update donut chart
            const donutChart = document.querySelector(".donut-chart");
            if (donutChart) {
                donutChart.setAttribute("data-normal", data.stats.normal_records);
                donutChart.setAttribute("data-attention", data.stats.attention_records);

                const normal = data.stats.normal_records;
                const attention = data.stats.attention_records;
                const total = normal + attention;

                if (total > 0) {
                    const normalDegrees = (normal / total) * 360;

                    donutChart.style.background = `
                        conic-gradient(
                            #0b9f6a 0deg,
                            #0b9f6a ${normalDegrees}deg,
                            #dc2626 ${normalDegrees}deg,
                            #dc2626 360deg
                        )
                    `;
                }

                // Update donut center text
                const donutCenter = donutChart.querySelector(".donut-center strong");
                if (donutCenter) {
                    donutCenter.textContent = total;
                }
            }

            // Update status trends bars
            const reportBarFills = document.querySelectorAll(".report-bar-fill");
            data.status_trends.forEach(function (item, index) {
                if (reportBarFills[index]) {
                    reportBarFills[index].setAttribute("data-percentage", item.percentage);
                    reportBarFills[index].style.width = item.percentage + "%";
                }
            });

        } catch (error) {
            console.log("Dashboard refresh skipped:", error);
        }
    }

    refreshDashboardData();
    setInterval(refreshDashboardData, 10000);

    /* ============================= */
    /* DASHBOARD BAR CHARTS */
    /* ============================= */

    const dashboardBarFills = document.querySelectorAll(".bar-fill");

    dashboardBarFills.forEach(function (bar) {
        const percentage = bar.getAttribute("data-percentage");

        if (percentage !== null) {
            bar.style.width = percentage + "%";
        }
    });

    /* ============================= */
    /* REPORTS PAGE BAR CHARTS */
    /* This fixes 0-count bars showing as full blue bars */
    /* ============================= */

    const reportBarFills = document.querySelectorAll(".report-bar-fill");

    reportBarFills.forEach(function (bar) {
        const percentage = bar.getAttribute("data-percentage");

        if (percentage !== null) {
            bar.style.width = percentage + "%";
        } else {
            bar.style.width = "0%";
        }
    });

    /* ============================= */
    /* DONUT CHART */
    /* ============================= */

    const donutChart = document.querySelector(".donut-chart");

    if (donutChart) {
        const normal = Number(donutChart.getAttribute("data-normal")) || 0;
        const attention = Number(donutChart.getAttribute("data-attention")) || 0;
        const total = normal + attention;

        if (total > 0) {
            const normalDegrees = (normal / total) * 360;

            donutChart.style.background = `
                conic-gradient(
                    #0b9f6a 0deg,
                    #0b9f6a ${normalDegrees}deg,
                    #dc2626 ${normalDegrees}deg,
                    #dc2626 360deg
                )
            `;
        }
    }

    /* ============================= */
    /* PRINT OR SAVE PDF BUTTON */
    /* ============================= */

    const printReportBtn = document.getElementById("printReportBtn");

    if (printReportBtn) {
        printReportBtn.addEventListener("click", function () {
            window.print();
        });
    }

    /* ============================= */
    /* REUSABLE INSTANT SEARCH */
    /* ============================= */

    function setupInstantSearch(inputId, clearButtonId, rowSelector, emptyStateId) {
        const input = document.getElementById(inputId);
        const clearButton = document.getElementById(clearButtonId);
        const rows = document.querySelectorAll(rowSelector);
        const emptyState = document.getElementById(emptyStateId);

        if (!input || rows.length === 0) {
            return;
        }

        function filterRows() {
            const searchValue = input.value.toLowerCase().trim();
            let visibleCount = 0;

            rows.forEach(function (row) {
                const rowText = row.getAttribute("data-search") || "";
                const searchableText = rowText.toLowerCase();

                if (searchableText.includes(searchValue)) {
                    row.style.display = "";
                    visibleCount += 1;
                } else {
                    row.style.display = "none";
                }
            });

            if (emptyState) {
                emptyState.style.display = visibleCount === 0 ? "block" : "none";
            }
        }

        input.addEventListener("input", filterRows);

        if (clearButton) {
            clearButton.addEventListener("click", function () {
                input.value = "";
                filterRows();
                input.focus();
            });
        }

        filterRows();
    }

    /* ============================= */
    /* PATIENT REGISTRY SEARCH */
    /* ============================= */

    setupInstantSearch(
        "patientRegistrySearch",
        "clearPatientRegistrySearch",
        ".patient-registry-row",
        "patientRegistryNoResults"
    );

    /* ============================= */
    /* EHR RECORDS SEARCH */
    /* ============================= */

    setupInstantSearch(
        "ehrPatientSearch",
        "clearEhrPatientSearch",
        ".ehr-patient-row",
        "ehrPatientNoResults"
    );

    /* ============================= */
    /* PATIENT RECORD HISTORY SEARCH */
    /* ============================= */

    setupInstantSearch(
        "patientRecordSearch",
        "clearPatientRecordSearch",
        ".patient-record-row",
        "patientRecordNoResults"
    );
});

/* ============================= */
/* CLEAN BIRTH DATE INPUT */
/* Manual MM/DD/YYYY + Calendar Icon */
/* ============================= */

document.addEventListener("DOMContentLoaded", function () {
    const birthDateText = document.getElementById("birthDateText");
    const birthDatePicker = document.getElementById("birthDatePicker");
    const openBirthDatePicker = document.getElementById("openBirthDatePicker");

    if (!birthDateText || !birthDatePicker || !openBirthDatePicker) {
        return;
    }

    function formatToMMDDYYYY(value) {
        const cleaned = value.replace(/\D/g, "").slice(0, 8);

        if (cleaned.length >= 5) {
            return cleaned.slice(0, 2) + "/" + cleaned.slice(2, 4) + "/" + cleaned.slice(4);
        }

        if (cleaned.length >= 3) {
            return cleaned.slice(0, 2) + "/" + cleaned.slice(2);
        }

        return cleaned;
    }

    function convertDatePickerToText(value) {
        if (!value) {
            return "";
        }

        const parts = value.split("-");
        const year = parts[0];
        const month = parts[1];
        const day = parts[2];

        return month + "/" + day + "/" + year;
    }

    function convertTextToDatePicker(value) {
        const parts = value.split("/");

        if (parts.length !== 3) {
            return "";
        }

        const month = parts[0];
        const day = parts[1];
        const year = parts[2];

        if (month.length !== 2 || day.length !== 2 || year.length !== 4) {
            return "";
        }

        return year + "-" + month + "-" + day;
    }

    birthDateText.addEventListener("input", function () {
        birthDateText.value = formatToMMDDYYYY(birthDateText.value);

        const pickerValue = convertTextToDatePicker(birthDateText.value);

        if (pickerValue) {
            birthDatePicker.value = pickerValue;
        }
    });

    openBirthDatePicker.addEventListener("click", function () {
        if (birthDatePicker.showPicker) {
            birthDatePicker.showPicker();
        } else {
            birthDatePicker.click();
        }
    });

    birthDatePicker.addEventListener("change", function () {
        birthDateText.value = convertDatePickerToText(birthDatePicker.value);
    });
});

/* ============================= */
/* SECURITY LOG SEARCH + FILTER */
/* ============================= */

document.addEventListener("DOMContentLoaded", function () {
    const searchInput = document.getElementById("securityLogSearch");
    const roleFilter = document.getElementById("securityRoleFilter");
    const actionFilter = document.getElementById("securityActionFilter");
    const clearButton = document.getElementById("clearSecurityFilters");
    const rows = document.querySelectorAll(".security-log-row");
    const noResults = document.getElementById("securityLogNoResults");

    if (!searchInput || !roleFilter || !actionFilter || rows.length === 0) {
        return;
    }

    function filterSecurityLogs() {
        const searchValue = searchInput.value.toLowerCase().trim();
        const selectedRole = roleFilter.value;
        const selectedAction = actionFilter.value;
        let visibleCount = 0;

        rows.forEach(function (row) {
            const rowText = (row.getAttribute("data-search") || "").toLowerCase();
            const rowRole = row.getAttribute("data-role") || "";
            const rowAction = (row.getAttribute("data-action") || "").toLowerCase();

            const matchesSearch = rowText.includes(searchValue);
            const matchesRole = selectedRole === "all" || rowRole === selectedRole;
            const matchesAction = selectedAction === "all" || rowAction.includes(selectedAction);

            if (matchesSearch && matchesRole && matchesAction) {
                row.style.display = "";
                visibleCount += 1;
            } else {
                row.style.display = "none";
            }
        });

        if (noResults) {
            noResults.style.display = visibleCount === 0 ? "block" : "none";
        }
    }

    searchInput.addEventListener("input", filterSecurityLogs);
    roleFilter.addEventListener("change", filterSecurityLogs);
    actionFilter.addEventListener("change", filterSecurityLogs);

    if (clearButton) {
        clearButton.addEventListener("click", function () {
            searchInput.value = "";
            roleFilter.value = "all";
            actionFilter.value = "all";
            filterSecurityLogs();
            searchInput.focus();
        });
    }

    filterSecurityLogs();
});

/* ============================= */
/* TOAST NOTIFICATIONS */
/* ============================= */

document.addEventListener("DOMContentLoaded", function () {
    const toasts = document.querySelectorAll(".toast-message");

    toasts.forEach(function (toast) {
        const closeButton = toast.querySelector(".toast-close");

        function removeToast() {
            toast.classList.add("hide");

            setTimeout(function () {
                toast.remove();
            }, 220);
        }

        if (closeButton) {
            closeButton.addEventListener("click", removeToast);
        }

        setTimeout(removeToast, 3500);
    });
});

/* ============================= */
/* USER MANAGEMENT SEARCH + FILTER */
/* ============================= */

document.addEventListener("DOMContentLoaded", function () {
    const userSearch = document.getElementById("userSearch");
    const userRoleFilter = document.getElementById("userRoleFilter");
    const clearUserFilters = document.getElementById("clearUserFilters");
    const userRows = document.querySelectorAll(".user-row");
    const userNoResults = document.getElementById("userNoResults");

    if (!userSearch || !userRoleFilter || userRows.length === 0) {
        return;
    }

    function filterUsers() {
        const searchValue = userSearch.value.toLowerCase().trim();
        const selectedRole = userRoleFilter.value;
        let visibleCount = 0;

        userRows.forEach(function (row) {
            const rowText = (row.getAttribute("data-search") || "").toLowerCase();
            const rowRole = row.getAttribute("data-role") || "";

            const matchesSearch = rowText.includes(searchValue);
            const matchesRole = selectedRole === "all" || rowRole === selectedRole;

            if (matchesSearch && matchesRole) {
                row.style.display = "";
                visibleCount += 1;
            } else {
                row.style.display = "none";
            }
        });

        if (userNoResults) {
            userNoResults.style.display = visibleCount === 0 ? "block" : "none";
        }
    }

    userSearch.addEventListener("input", filterUsers);
    userRoleFilter.addEventListener("change", filterUsers);

    if (clearUserFilters) {
        clearUserFilters.addEventListener("click", function () {
            userSearch.value = "";
            userRoleFilter.value = "all";
            filterUsers();
            userSearch.focus();
        });
    }

    filterUsers();
});

/* ============================= */
/* KIOSK CLOCK */
/* ============================= */

document.addEventListener("DOMContentLoaded", function () {
    const kioskClock = document.getElementById("kioskClock");

    if (!kioskClock) {
        return;
    }

    function updateKioskClock() {
        const now = new Date();

        kioskClock.textContent = now.toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit"
        });
    }

    updateKioskClock();
    setInterval(updateKioskClock, 1000);
});

/* ===================================== */
/* KIOSK TEMPERATURE SIMULATION */
/* ===================================== */

document.addEventListener("DOMContentLoaded", function () {
    const openBtn = document.getElementById("openTempInstructionsBtn");
    const modal = document.getElementById("tempInstructionModal");
    const prevBtn = document.getElementById("tempPrevBtn");
    const nextBtn = document.getElementById("tempNextBtn");

    const stepTitle = document.getElementById("tempStepTitle");
    const stepText = document.getElementById("tempStepText");
    const stepIcon = document.getElementById("tempStepIcon");

    const tempMessage = document.getElementById("tempMessage");
    const tempValue = document.getElementById("tempValue");
    const tempStatus = document.getElementById("tempStatus");
    const tempInput = document.getElementById("temperatureValueInput");

    const startActions = document.getElementById("tempStartActions");
    const measuringActions = document.getElementById("tempMeasuringActions");
    const resultActions = document.getElementById("tempResultActions");

    const cancelBtn = document.getElementById("cancelTempBtn");
    const retryBtn = document.getElementById("retryTempBtn");
    const retrySavedBtn = document.getElementById("retrySavedTempBtn");

    if (!openBtn && !retrySavedBtn) {
        return;
    }

    const steps = [
        {
            icon: '<i class="fa-solid fa-temperature-three-quarters"></i>',
            title: "Step 1: Prepare",
            text: "Make sure your forehead is clean, dry, and free from sweat or cosmetics."
        },
        {
            icon: '<i class="fa-solid fa-ruler"></i>',
            title: "Step 2: Positioning",
            text: "Hold the temperature sensor 1 to 2 cm away from the center of your forehead."
        },
        {
            icon: '<i class="fa-solid fa-check"></i>',
            title: "Step 3: Measurement",
            text: "Keep still while the sensor reads your temperature. The process will only take a few seconds."
        }
    ];

    let currentStep = 0;
    let measuringTimer = null;

    function updateModalStep() {
        stepIcon.innerHTML = steps[currentStep].icon;
        stepTitle.textContent = steps[currentStep].title;
        stepText.textContent = steps[currentStep].text;

        document.querySelectorAll(".temp-step-dots span").forEach(function (dot, index) {
            dot.classList.toggle("active", index === currentStep);
        });

        prevBtn.disabled = currentStep === 0;

        if (currentStep === steps.length - 1) {
            nextBtn.textContent = "Start Measurement";
        } else {
            nextBtn.textContent = "Next";
        }
    }

    function openInstructionModal() {
        currentStep = 0;
        updateModalStep();
        modal.classList.remove("hidden");
    }

    function resetMeasurementScreen() {
        if (tempMessage) {
            tempMessage.textContent = "Ready to measure. Click Start to begin.";
        }

        if (tempValue) {
            tempValue.textContent = "--.- °C";
            tempValue.classList.remove("measuring", "complete");
        }

        if (tempStatus) {
            tempStatus.textContent = "";
            tempStatus.className = "temp-status";
        }

        if (tempInput) {
            tempInput.value = "";
        }

        if (startActions) {
            startActions.classList.remove("hidden");
        }

        if (measuringActions) {
            measuringActions.classList.add("hidden");
        }

        if (resultActions) {
            resultActions.classList.add("hidden");
        }
    }

    function startMeasurement() {
        if (!tempMessage || !tempValue || !tempStatus || !tempInput) {
            return;
        }

        if (startActions) {
            startActions.classList.add("hidden");
        }

        if (resultActions) {
            resultActions.classList.add("hidden");
        }

        if (measuringActions) {
            measuringActions.classList.remove("hidden");
        }

        tempMessage.textContent = "Measuring... Please hold still.";
        tempValue.textContent = "--.- °C";
        tempValue.classList.add("measuring");
        tempValue.classList.remove("complete");

        tempStatus.textContent = "";
        tempStatus.className = "temp-status";
        tempInput.value = "";

        measuringTimer = setTimeout(function () {
            const result = generateTemperatureResult();
            const status = getTemperatureStatus(result);

            tempMessage.textContent = "Measurement complete.";
            tempValue.textContent = result.toFixed(1) + " °C";
            tempValue.classList.remove("measuring");
            tempValue.classList.add("complete");

            tempStatus.textContent = status.label;
            tempStatus.className = "temp-status " + status.className;

            tempInput.value = result.toFixed(1);

            if (measuringActions) {
                measuringActions.classList.add("hidden");
            }

            if (resultActions) {
                resultActions.classList.remove("hidden");
            }
        }, 3000);
    }

    function generateTemperatureResult() {
        const results = [36.2, 36.3, 36.4, 36.5, 36.6, 36.7];
        const randomIndex = Math.floor(Math.random() * results.length);
        return results[randomIndex];
    }

    function getTemperatureStatus(value) {
        if (value < 36.0) {
            return {
                label: "LOW TEMPERATURE",
                className: "warning"
            };
        }

        if (value <= 37.5) {
            return {
                label: "NORMAL TEMPERATURE",
                className: "normal"
            };
        }

        return {
            label: "HIGH TEMPERATURE",
            className: "danger"
        };
    }

    if (openBtn) {
        openBtn.addEventListener("click", openInstructionModal);
    }

    if (retrySavedBtn) {
        retrySavedBtn.addEventListener("click", function () {
            window.location.href = window.location.href;
        });
    }

    if (prevBtn) {
        prevBtn.addEventListener("click", function () {
            if (currentStep > 0) {
                currentStep--;
                updateModalStep();
            }
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener("click", function () {
            if (currentStep < steps.length - 1) {
                currentStep++;
                updateModalStep();
            } else {
                modal.classList.add("hidden");
                startMeasurement();
            }
        });
    }

    if (cancelBtn) {
        cancelBtn.addEventListener("click", function () {
            clearTimeout(measuringTimer);
            resetMeasurementScreen();
        });
    }

    if (retryBtn) {
        retryBtn.addEventListener("click", function () {
            startMeasurement();
        });
    }
});

/* ===================================== */
/* KIOSK BLOOD PRESSURE SIMULATION */
/* ===================================== */

document.addEventListener("DOMContentLoaded", function () {
    const openBtn = document.getElementById("openBpInstructionsBtn");
    const modal = document.getElementById("bpInstructionModal");
    const prevBtn = document.getElementById("bpPrevBtn");
    const nextBtn = document.getElementById("bpNextBtn");

    const stepTitle = document.getElementById("bpStepTitle");
    const stepText = document.getElementById("bpStepText");
    const stepIcon = document.getElementById("bpStepIcon");

    const bpMessage = document.getElementById("bpMessage");
    const bpValue = document.getElementById("bpValue");
    const bpPulse = document.getElementById("bpPulse");
    const bpStatus = document.getElementById("bpStatus");

    const systolicInput = document.getElementById("systolicValueInput");
    const diastolicInput = document.getElementById("diastolicValueInput");
    const pulseInput = document.getElementById("pulseValueInput");

    const startActions = document.getElementById("bpStartActions");
    const measuringActions = document.getElementById("bpMeasuringActions");
    const resultActions = document.getElementById("bpResultActions");

    const cancelBtn = document.getElementById("cancelBpBtn");
    const retryBtn = document.getElementById("retryBpBtn");

    if (!openBtn) {
        return;
    }

    const steps = [
        {
            icon: '<i class="fa-solid fa-chair"></i>',
            title: "Step 1: Sit Properly",
            text: "Sit comfortably with your back supported and your feet flat on the floor."
        },
        {
            icon: '<i class="fa-solid fa-hand"></i>',
            title: "Step 2: Position Your Arm",
            text: "Place your arm on the kiosk arm rest. Keep it relaxed and level with your heart."
        },
        {
            icon: '<i class="fa-solid fa-heart-pulse"></i>',
            title: "Step 3: Stay Still",
            text: "Do not move or talk while the blood pressure monitor is taking your reading."
        }
    ];

    let currentStep = 0;
    let measuringTimer = null;

    function updateModalStep() {
        stepIcon.innerHTML = steps[currentStep].icon;
        stepTitle.textContent = steps[currentStep].title;
        stepText.textContent = steps[currentStep].text;

        document.querySelectorAll(".bp-step-dots span").forEach(function (dot, index) {
            dot.classList.toggle("active", index === currentStep);
        });

        prevBtn.disabled = currentStep === 0;

        if (currentStep === steps.length - 1) {
            nextBtn.textContent = "Start Measurement";
        } else {
            nextBtn.textContent = "Next";
        }
    }

    function openInstructionModal() {
        currentStep = 0;
        updateModalStep();
        modal.classList.remove("hidden");
    }

    function resetMeasurementScreen() {
        bpMessage.textContent = "Ready to measure. Click Start to begin.";
        bpValue.innerHTML = '--/--<small>mmHg</small>';
        bpValue.classList.remove("measuring", "complete");
        bpPulse.textContent = "Pulse: -- bpm";
        bpStatus.textContent = "";
        bpStatus.className = "bp-status";

        systolicInput.value = "";
        diastolicInput.value = "";
        pulseInput.value = "";

        startActions.classList.remove("hidden");
        measuringActions.classList.add("hidden");
        resultActions.classList.add("hidden");
    }

    function startMeasurement() {
        startActions.classList.add("hidden");
        resultActions.classList.add("hidden");
        measuringActions.classList.remove("hidden");

        bpMessage.textContent = "Measuring... Please stay still.";
        bpValue.innerHTML = '--/--<small>mmHg</small>';
        bpValue.classList.add("measuring");
        bpValue.classList.remove("complete");
        bpPulse.textContent = "Pulse: -- bpm";
        bpStatus.textContent = "";
        bpStatus.className = "bp-status";

        systolicInput.value = "";
        diastolicInput.value = "";
        pulseInput.value = "";

        measuringTimer = setTimeout(function () {
            const result = generateBloodPressureResult();
            const status = getBloodPressureStatus(result.systolic, result.diastolic);

            bpMessage.textContent = "Measurement complete.";
            bpValue.innerHTML = result.systolic + "/" + result.diastolic + "<small>mmHg</small>";
            bpValue.classList.remove("measuring");
            bpValue.classList.add("complete");

            bpPulse.textContent = "Pulse: " + result.pulse + " bpm";

            bpStatus.textContent = status.label;
            bpStatus.className = "bp-status " + status.className;

            systolicInput.value = result.systolic;
            diastolicInput.value = result.diastolic;
            pulseInput.value = result.pulse;

            measuringActions.classList.add("hidden");
            resultActions.classList.remove("hidden");
        }, 3500);
    }

    function generateBloodPressureResult() {
        const normalResults = [
            { systolic: 118, diastolic: 76, pulse: 76 },
            { systolic: 120, diastolic: 80, pulse: 78 },
            { systolic: 122, diastolic: 79, pulse: 74 },
            { systolic: 116, diastolic: 75, pulse: 72 },
            { systolic: 124, diastolic: 82, pulse: 80 }
        ];

        const randomIndex = Math.floor(Math.random() * normalResults.length);
        return normalResults[randomIndex];
    }

    function getBloodPressureStatus(systolic, diastolic) {
        if (systolic < 90 || diastolic < 60) {
            return {
                label: "LOW BLOOD PRESSURE",
                className: "warning"
            };
        }

        if (systolic >= 140 || diastolic >= 90) {
            return {
                label: "HIGH BLOOD PRESSURE",
                className: "danger"
            };
        }

        return {
            label: "NORMAL BLOOD PRESSURE",
            className: "normal"
        };
    }

    openBtn.addEventListener("click", openInstructionModal);

    prevBtn.addEventListener("click", function () {
        if (currentStep > 0) {
            currentStep--;
            updateModalStep();
        }
    });

    nextBtn.addEventListener("click", function () {
        if (currentStep < steps.length - 1) {
            currentStep++;
            updateModalStep();
        } else {
            modal.classList.add("hidden");
            startMeasurement();
        }
    });

    cancelBtn.addEventListener("click", function () {
        clearTimeout(measuringTimer);
        resetMeasurementScreen();
    });

    retryBtn.addEventListener("click", function () {
        startMeasurement();
    });
});

/* ===================================== */
/* KIOSK HEIGHT SIMULATION */
/* ===================================== */

document.addEventListener("DOMContentLoaded", function () {
    const openBtn = document.getElementById("openHeightInstructionsBtn");
    const modal = document.getElementById("heightInstructionModal");
    const prevBtn = document.getElementById("heightPrevBtn");
    const nextBtn = document.getElementById("heightNextBtn");

    const stepTitle = document.getElementById("heightStepTitle");
    const stepText = document.getElementById("heightStepText");
    const stepIcon = document.getElementById("heightStepIcon");

    const heightMessage = document.getElementById("heightMessage");
    const heightValue = document.getElementById("heightValue");
    const heightStatus = document.getElementById("heightStatus");
    const heightInput = document.getElementById("heightValueInput");

    const startActions = document.getElementById("heightStartActions");
    const measuringActions = document.getElementById("heightMeasuringActions");
    const resultActions = document.getElementById("heightResultActions");

    const cancelBtn = document.getElementById("cancelHeightBtn");
    const retryBtn = document.getElementById("retryHeightBtn");

    if (!openBtn) {
        return;
    }

    const steps = [
        {
            icon: '<i class="fa-solid fa-ruler-vertical"></i>',
            title: "Step 1: Stand Straight",
            text: "Stand on the marked area with your back upright and your feet flat on the floor."
        },
        {
            icon: '<i class="fa-solid fa-person"></i>',
            title: "Step 2: Face Forward",
            text: "Keep your head straight, face forward, and avoid bending your knees."
        },
        {
            icon: '<i class="fa-solid fa-check"></i>',
            title: "Step 3: Stay Still",
            text: "Remain still while the height sensor reads your measurement."
        }
    ];

    let currentStep = 0;
    let measuringTimer = null;

    function updateModalStep() {
        stepIcon.innerHTML = steps[currentStep].icon;
        stepTitle.textContent = steps[currentStep].title;
        stepText.textContent = steps[currentStep].text;

        document.querySelectorAll(".height-step-dots span").forEach(function (dot, index) {
            dot.classList.toggle("active", index === currentStep);
        });

        prevBtn.disabled = currentStep === 0;

        if (currentStep === steps.length - 1) {
            nextBtn.textContent = "Start Measurement";
        } else {
            nextBtn.textContent = "Next";
        }
    }

    function openInstructionModal() {
        currentStep = 0;
        updateModalStep();
        modal.classList.remove("hidden");
    }

    function resetMeasurementScreen() {
        heightMessage.textContent = "Ready to measure. Click Start to begin.";
        heightValue.innerHTML = '--.-<small>cm</small>';
        heightValue.classList.remove("measuring", "complete");
        heightStatus.textContent = "";
        heightStatus.className = "height-status";
        heightInput.value = "";

        startActions.classList.remove("hidden");
        measuringActions.classList.add("hidden");
        resultActions.classList.add("hidden");
    }

    function startMeasurement() {
        startActions.classList.add("hidden");
        resultActions.classList.add("hidden");
        measuringActions.classList.remove("hidden");

        heightMessage.textContent = "Measuring... Please stand still.";
        heightValue.innerHTML = '--.-<small>cm</small>';
        heightValue.classList.add("measuring");
        heightValue.classList.remove("complete");
        heightStatus.textContent = "";
        heightStatus.className = "height-status";
        heightInput.value = "";

        measuringTimer = setTimeout(function () {
            const result = generateHeightResult();
            const status = getHeightStatus(result);

            heightMessage.textContent = "Measurement complete.";
            heightValue.innerHTML = result.toFixed(1) + "<small>cm</small>";
            heightValue.classList.remove("measuring");
            heightValue.classList.add("complete");

            heightStatus.textContent = status.label;
            heightStatus.className = "height-status " + status.className;
            heightInput.value = result.toFixed(1);

            measuringActions.classList.add("hidden");
            resultActions.classList.remove("hidden");
        }, 3000);
    }

    function generateHeightResult() {
        const results = [152.4, 155.6, 158.2, 160.5, 162.7, 165.3, 168.1, 170.4];
        const randomIndex = Math.floor(Math.random() * results.length);
        return results[randomIndex];
    }

    function getHeightStatus(value) {
        if (value < 120) {
            return {
                label: "BELOW AVERAGE HEIGHT",
                className: "warning"
            };
        }

        if (value <= 190) {
            return {
                label: "HEIGHT RECORDED",
                className: "normal"
            };
        }

        return {
            label: "ABOVE AVERAGE HEIGHT",
            className: "danger"
        };
    }

    openBtn.addEventListener("click", openInstructionModal);

    prevBtn.addEventListener("click", function () {
        if (currentStep > 0) {
            currentStep--;
            updateModalStep();
        }
    });

    nextBtn.addEventListener("click", function () {
        if (currentStep < steps.length - 1) {
            currentStep++;
            updateModalStep();
        } else {
            modal.classList.add("hidden");
            startMeasurement();
        }
    });

    cancelBtn.addEventListener("click", function () {
        clearTimeout(measuringTimer);
        resetMeasurementScreen();
    });

    retryBtn.addEventListener("click", function () {
        startMeasurement();
    });
});

/* ===================================== */
/* KIOSK WEIGHT SIMULATION WITH SCALE ZEROING + STEP-ON COUNTDOWN */
/* ===================================== */

document.addEventListener("DOMContentLoaded", function () {
    const openBtn = document.getElementById("openWeightInstructionsBtn");
    const modal = document.getElementById("weightInstructionModal");
    const prevBtn = document.getElementById("weightPrevBtn");
    const nextBtn = document.getElementById("weightNextBtn");

    const stepTitle = document.getElementById("weightStepTitle");
    const stepText = document.getElementById("weightStepText");
    const stepIcon = document.getElementById("weightStepIcon");

    const weightMessage = document.getElementById("weightMessage");
    const weightValue = document.getElementById("weightValue");
    const weightStatus = document.getElementById("weightStatus");
    const weightInput = document.getElementById("weightValueInput");

    const startActions = document.getElementById("weightStartActions");
    const measuringActions = document.getElementById("weightMeasuringActions");
    const resultActions = document.getElementById("weightResultActions");

    const cancelBtn = document.getElementById("cancelWeightBtn");
    const retryBtn = document.getElementById("retryWeightBtn");

    if (!openBtn) {
        return;
    }

    const steps = [
        {
            icon: '<i class="fa-solid fa-shoe-prints"></i>',
            title: "Step 1: Step Off First",
            text: "Please step away from the weighing platform before starting. This allows the scale to refresh and reset to zero."
        },
        {
            icon: '<i class="fa-solid fa-weight-scale"></i>',
            title: "Step 2: Step on the Scale",
            text: "When the screen tells you to step on, stand on the weighing scale with both feet properly positioned."
        },
        {
            icon: '<i class="fa-solid fa-person-standing"></i>',
            title: "Step 3: Stand Still",
            text: "Keep your body still and avoid holding onto anything while your weight is being measured."
        }
    ];

    let currentStep = 0;
    let calibrationTimer = null;
    let stepOnTimer = null;
    let measuringTimer = null;
    let calibrationInterval = null;
    let stepOnInterval = null;

    function updateModalStep() {
        stepIcon.innerHTML = steps[currentStep].icon;
        stepTitle.textContent = steps[currentStep].title;
        stepText.textContent = steps[currentStep].text;

        document.querySelectorAll(".weight-step-dots span").forEach(function (dot, index) {
            dot.classList.toggle("active", index === currentStep);
        });

        prevBtn.disabled = currentStep === 0;

        if (currentStep === steps.length - 1) {
            nextBtn.textContent = "Start Measurement";
        } else {
            nextBtn.textContent = "Next";
        }
    }

    function openInstructionModal() {
        currentStep = 0;
        updateModalStep();
        modal.classList.remove("hidden");
    }

    function clearAllWeightTimers() {
        clearTimeout(calibrationTimer);
        clearTimeout(stepOnTimer);
        clearTimeout(measuringTimer);
        clearInterval(calibrationInterval);
        clearInterval(stepOnInterval);
    }

    function resetMeasurementScreen() {
        clearAllWeightTimers();

        weightMessage.textContent = "Ready to measure. Click Start to begin.";
        weightValue.innerHTML = '--.-<small>kg</small>';
        weightValue.classList.remove("measuring", "complete");
        weightStatus.textContent = "";
        weightStatus.className = "weight-status";
        weightInput.value = "";

        startActions.classList.remove("hidden");
        measuringActions.classList.add("hidden");
        resultActions.classList.add("hidden");
    }

    function startMeasurement() {
        clearAllWeightTimers();

        startActions.classList.add("hidden");
        resultActions.classList.add("hidden");
        measuringActions.classList.remove("hidden");

        let calibrationCountdown = 5;

        weightMessage.textContent = "Please step off the platform. Calibrating scale...";
        weightValue.innerHTML = calibrationCountdown + '<small>sec</small>';
        weightValue.classList.add("measuring");
        weightValue.classList.remove("complete");
        weightStatus.textContent = "ZEROING SCALE";
        weightStatus.className = "weight-status warning";
        weightInput.value = "";

        calibrationInterval = setInterval(function () {
            calibrationCountdown -= 1;

            if (calibrationCountdown > 0) {
                weightValue.innerHTML = calibrationCountdown + '<small>sec</small>';
            }
        }, 1000);

        calibrationTimer = setTimeout(function () {
            clearInterval(calibrationInterval);
            showStepOnCountdown();
        }, 5000);
    }

    function showStepOnCountdown() {
        let stepOnCountdown = 5;

        weightMessage.textContent = "Step on the platform now.";
        weightValue.innerHTML = stepOnCountdown + '<small>sec</small>';
        weightStatus.textContent = "PLEASE STEP ON";
        weightStatus.className = "weight-status warning";

        stepOnInterval = setInterval(function () {
            stepOnCountdown -= 1;

            if (stepOnCountdown > 0) {
                weightValue.innerHTML = stepOnCountdown + '<small>sec</small>';
            }
        }, 1000);

        stepOnTimer = setTimeout(function () {
            clearInterval(stepOnInterval);
            measureWeight();
        }, 5000);
    }

    function measureWeight() {
        weightMessage.textContent = "Measuring... Please stand still.";
        weightValue.innerHTML = '--.-<small>kg</small>';
        weightStatus.textContent = "MEASURING WEIGHT";
        weightStatus.className = "weight-status warning";

        measuringTimer = setTimeout(function () {
            const result = generateWeightResult();
            const status = getWeightStatus(result);

            weightMessage.textContent = "Measurement complete.";
            weightValue.innerHTML = result.toFixed(1) + "<small>kg</small>";
            weightValue.classList.remove("measuring");
            weightValue.classList.add("complete");

            weightStatus.textContent = status.label;
            weightStatus.className = "weight-status " + status.className;
            weightInput.value = result.toFixed(1);

            measuringActions.classList.add("hidden");
            resultActions.classList.remove("hidden");
        }, 3000);
    }

    function generateWeightResult() {
        const results = [47.8, 50.2, 52.5, 55.0, 58.4, 60.7, 63.1, 66.5, 70.2];
        const randomIndex = Math.floor(Math.random() * results.length);
        return results[randomIndex];
    }

    function getWeightStatus(value) {
        if (value <= 0) {
            return {
                label: "INVALID WEIGHT",
                className: "danger"
            };
        }

        return {
            label: "WEIGHT RECORDED",
            className: "normal"
        };
    }

    openBtn.addEventListener("click", openInstructionModal);

    prevBtn.addEventListener("click", function () {
        if (currentStep > 0) {
            currentStep--;
            updateModalStep();
        }
    });

    nextBtn.addEventListener("click", function () {
        if (currentStep < steps.length - 1) {
            currentStep++;
            updateModalStep();
        } else {
            modal.classList.add("hidden");
            startMeasurement();
        }
    });

    cancelBtn.addEventListener("click", function () {
        resetMeasurementScreen();
    });

    retryBtn.addEventListener("click", function () {
        startMeasurement();
    });
});

/* ===================================== */
/* KIOSK BMI CALCULATION */
/* ===================================== */

document.addEventListener("DOMContentLoaded", function () {
    const calculateBtn = document.getElementById("calculateBmiBtn");
    const retryBtn = document.getElementById("retryBmiBtn");
    const recalculateBtn = document.getElementById("recalculateBmiBtn");

    const bmiMessage = document.getElementById("bmiMessage");
    const bmiValue = document.getElementById("bmiValue");
    const bmiStatus = document.getElementById("bmiStatus");

    const startActions = document.getElementById("bmiStartActions");
    const resultActions = document.getElementById("bmiResultActions");

    if (!calculateBtn && !recalculateBtn) {
        return;
    }

    function getStatusClass(category) {
        if (category === "Normal") {
            return "normal";
        }

        if (category === "Invalid") {
            return "danger";
        }

        return "warning";
    }

    function calculateBmiDisplay() {
        const calculatedBmi = bmiValue.getAttribute("data-bmi");
        const bmiCategory = bmiValue.getAttribute("data-category");
        const bmiStatusText = bmiValue.getAttribute("data-status");

        bmiMessage.textContent = "Calculating BMI from height and weight...";
        bmiValue.innerHTML = '--.-<small>kg/m²</small>';
        bmiValue.classList.add("calculating");
        bmiValue.classList.remove("complete");

        bmiStatus.textContent = "";
        bmiStatus.className = "bmi-status";

        startActions.classList.add("hidden");
        resultActions.classList.add("hidden");

        setTimeout(function () {
            bmiMessage.textContent = "BMI calculation complete.";
            bmiValue.innerHTML = calculatedBmi + "<small>kg/m²</small>";
            bmiValue.classList.remove("calculating");
            bmiValue.classList.add("complete");

            bmiStatus.textContent = bmiStatusText;
            bmiStatus.className = "bmi-status " + getStatusClass(bmiCategory);

            resultActions.classList.remove("hidden");
        }, 1200);
    }

    if (calculateBtn) {
        calculateBtn.addEventListener("click", calculateBmiDisplay);
    }

    if (retryBtn) {
        retryBtn.addEventListener("click", calculateBmiDisplay);
    }

    if (recalculateBtn) {
        recalculateBtn.addEventListener("click", function () {
            window.location.href = "{{ url_for('kiosk_bmi_page') }}";
        });
    }
});

/* ===================================== */
/* KIOSK OXYGEN SATURATION SIMULATION */
/* ===================================== */

document.addEventListener("DOMContentLoaded", function () {
    const openBtn = document.getElementById("openSpo2InstructionsBtn");
    const modal = document.getElementById("spo2InstructionModal");
    const prevBtn = document.getElementById("spo2PrevBtn");
    const nextBtn = document.getElementById("spo2NextBtn");

    const stepTitle = document.getElementById("spo2StepTitle");
    const stepText = document.getElementById("spo2StepText");
    const stepIcon = document.getElementById("spo2StepIcon");

    const spo2Message = document.getElementById("spo2Message");
    const spo2Value = document.getElementById("spo2Value");
    const spo2Status = document.getElementById("spo2Status");
    const spo2Input = document.getElementById("spo2ValueInput");

    const startActions = document.getElementById("spo2StartActions");
    const measuringActions = document.getElementById("spo2MeasuringActions");
    const resultActions = document.getElementById("spo2ResultActions");

    const cancelBtn = document.getElementById("cancelSpo2Btn");
    const retryBtn = document.getElementById("retrySpo2Btn");

    if (!openBtn) {
        return;
    }

    const steps = [
        {
            icon: '<i class="fa-solid fa-hand"></i>',
            title: "Step 1: Prepare Your Finger",
            text: "Make sure your finger is clean, dry, and free from nail polish or anything blocking the sensor."
        },
        {
            icon: '<i class="fa-solid fa-fingerprint"></i>',
            title: "Step 2: Place Your Finger",
            text: "Insert your finger properly into the pulse oximeter sensor. Keep it relaxed and centered."
        },
        {
            icon: '<i class="fa-solid fa-lungs"></i>',
            title: "Step 3: Stay Still",
            text: "Keep your finger still while the oxygen saturation reading is being measured."
        }
    ];

    let currentStep = 0;
    let measuringTimer = null;

    function updateModalStep() {
        stepIcon.innerHTML = steps[currentStep].icon;
        stepTitle.textContent = steps[currentStep].title;
        stepText.textContent = steps[currentStep].text;

        document.querySelectorAll(".spo2-step-dots span").forEach(function (dot, index) {
            dot.classList.toggle("active", index === currentStep);
        });

        prevBtn.disabled = currentStep === 0;

        if (currentStep === steps.length - 1) {
            nextBtn.textContent = "Start Measurement";
        } else {
            nextBtn.textContent = "Next";
        }
    }

    function openInstructionModal() {
        currentStep = 0;
        updateModalStep();
        modal.classList.remove("hidden");
    }

    function resetMeasurementScreen() {
        clearTimeout(measuringTimer);

        spo2Message.textContent = "Ready to measure. Click Start to begin.";
        spo2Value.innerHTML = '--<small>%</small>';
        spo2Value.classList.remove("measuring", "complete");
        spo2Status.textContent = "";
        spo2Status.className = "spo2-status";
        spo2Input.value = "";

        startActions.classList.remove("hidden");
        measuringActions.classList.add("hidden");
        resultActions.classList.add("hidden");
    }

    function startMeasurement() {
        startActions.classList.add("hidden");
        resultActions.classList.add("hidden");
        measuringActions.classList.remove("hidden");

        spo2Message.textContent = "Measuring... Please keep your finger still.";
        spo2Value.innerHTML = '--<small>%</small>';
        spo2Value.classList.add("measuring");
        spo2Value.classList.remove("complete");
        spo2Status.textContent = "READING OXYGEN LEVEL";
        spo2Status.className = "spo2-status warning";
        spo2Input.value = "";

        measuringTimer = setTimeout(function () {
            const result = generateSpo2Result();
            const status = getSpo2Status(result);

            spo2Message.textContent = "Measurement complete.";
            spo2Value.innerHTML = result + "<small>%</small>";
            spo2Value.classList.remove("measuring");
            spo2Value.classList.add("complete");

            spo2Status.textContent = status.label;
            spo2Status.className = "spo2-status " + status.className;
            spo2Input.value = result;

            measuringActions.classList.add("hidden");
            resultActions.classList.remove("hidden");
        }, 3000);
    }

    function generateSpo2Result() {
        const results = [96, 97, 98, 99];
        const randomIndex = Math.floor(Math.random() * results.length);
        return results[randomIndex];
    }

    function getSpo2Status(value) {
        if (value < 95) {
            return {
                label: "LOW OXYGEN SATURATION",
                className: "danger"
            };
        }

        if (value <= 100) {
            return {
                label: "NORMAL OXYGEN SATURATION",
                className: "normal"
            };
        }

        return {
            label: "INVALID OXYGEN SATURATION",
            className: "danger"
        };
    }

    openBtn.addEventListener("click", openInstructionModal);

    prevBtn.addEventListener("click", function () {
        if (currentStep > 0) {
            currentStep--;
            updateModalStep();
        }
    });

    nextBtn.addEventListener("click", function () {
        if (currentStep < steps.length - 1) {
            currentStep++;
            updateModalStep();
        } else {
            modal.classList.add("hidden");
            startMeasurement();
        }
    });

    cancelBtn.addEventListener("click", function () {
        resetMeasurementScreen();
    });

    retryBtn.addEventListener("click", function () {
        startMeasurement();
    });
});

/* ===================================== */
/* KIOSK PRINT RESULT BUTTON */
/* ===================================== */

document.addEventListener("DOMContentLoaded", function () {
    const printResultBtn = document.getElementById("printResultBtn");

    if (!printResultBtn) {
        return;
    }

    printResultBtn.addEventListener("click", function () {
        window.print();
    });
});

/* ============================= */
/* ALL-VITALS TREND & LONGITUDINAL ANALYTICS ENGINE */
/* Supports: Blood Pressure (Systolic/Diastolic dual lines), */
/* Heart Rate, SpO2, Temperature, BMI, and Weight with clinical threshold bands, */
/* interactive tooltips, multi-range filtering, and patient filtering. */
/* ============================= */

document.addEventListener("DOMContentLoaded", function () {
    // Floating tooltip singleton
    let chartTooltip = document.getElementById("vitalsGlobalTooltip");
    if (!chartTooltip) {
        chartTooltip = document.createElement("div");
        chartTooltip.id = "vitalsGlobalTooltip";
        chartTooltip.className = "vitals-chart-tooltip";
        chartTooltip.style.display = "none";
        document.body.appendChild(chartTooltip);
    }

    function parseRecordDate(value) {
        if (!value) return null;

        const parts = String(value).trim().match(/^(\d{4})-(\d{2})-(\d{2})\s+(\d{1,2}):(\d{2})\s*(AM|PM)?$/i);
        if (!parts) {
            const fallbackDate = new Date(value);
            return Number.isNaN(fallbackDate.getTime()) ? null : fallbackDate;
        }

        let hour = Number(parts[4]);
        const minute = Number(parts[5]);
        const meridiem = parts[6] ? parts[6].toUpperCase() : null;

        if (meridiem === "PM" && hour !== 12) hour += 12;
        if (meridiem === "AM" && hour === 12) hour = 0;

        return new Date(
            Number(parts[1]),
            Number(parts[2]) - 1,
            Number(parts[3]),
            hour,
            minute
        );
    }

    function formatShortDate(date) {
        return date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric"
        });
    }

    function formatDateTime(date) {
        return date.toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric"
        }) + " " + date.toLocaleTimeString("en-US", {
            hour: "numeric",
            minute: "2-digit"
        });
    }

    function getStartOfWeek(date) {
        const start = new Date(date);
        const day = start.getDay();
        start.setDate(start.getDate() - day);
        start.setHours(0, 0, 0, 0);
        return start;
    }

    function getEndOfDay(date) {
        const end = new Date(date);
        end.setHours(23, 59, 59, 999);
        return end;
    }

    function getDateFromInput(value, endOfDay) {
        if (!value) return null;
        const parts = value.split("-");
        if (parts.length !== 3) return null;

        const date = new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]));
        if (endOfDay) return getEndOfDay(date);
        date.setHours(0, 0, 0, 0);
        return date;
    }

    // Initialize all vital chart instances on the page
    const chartContainers = document.querySelectorAll(
        ".vitals-trend-chart-container, #vitalsLineChart, #bmiLineChart"
    );

    chartContainers.forEach(function (container) {
        setupVitalsChartInstance(container);
    });

    function setupVitalsChartInstance(container) {
        const rootCard = container.closest(".vitals-visualization-panel, .bmi-visualization-panel, .panel") || container.parentElement;

        const chartSvg = container.querySelector("svg") || document.getElementById(container.id + "Svg") || document.getElementById("bmiLineChartSvg");
        if (!chartSvg) return;

        // Metric selector tabs or dropdown
        const metricTabs = rootCard.querySelectorAll(".metric-tab-btn");
        const metricSelect = rootCard.querySelector(".vitals-metric-select");

        // Range selector & custom range
        const chartRange = rootCard.querySelector(".vitals-chart-range, #bmiChartRange");
        const customRangeBox = rootCard.querySelector(".vitals-custom-range, #bmiCustomRange");
        const startDateInput = rootCard.querySelector(".vitals-start-date, #bmiStartDate");
        const endDateInput = rootCard.querySelector(".vitals-end-date, #bmiEndDate");

        // Patient filter dropdown (if present)
        const patientFilter = rootCard.querySelector(".vitals-patient-filter, #vitalsPatientFilter");

        // Note / description paragraph
        const chartNote = rootCard.querySelector(".vitals-chart-note, #bmiLineChartNote");

        // Dynamic stats banner elements (if present)
        const statAvgEl = rootCard.querySelector("[data-stat='avg']");
        const statTargetEl = rootCard.querySelector("[data-stat='target-pct']");
        const statMinEl = rootCard.querySelector("[data-stat='min']");
        const statMaxEl = rootCard.querySelector("[data-stat='max']");
        const statCountEl = rootCard.querySelector("[data-stat='count']");
        const legendContainer = rootCard.querySelector(".vitals-chart-legend, .bmi-chart-legend");

        let activeMetric = container.getAttribute("data-default-metric") || "bp";
        // Default to bp unless it's strictly legacy bmi container with only bmi
        if (container.id === "bmiLineChart" && !container.hasAttribute("data-default-metric") && !rootCard.querySelector(".metric-tab-btn")) {
            activeMetric = "bmi";
        }

        let rawRecords = [];
        try {
            rawRecords = JSON.parse(container.getAttribute("data-records") || "[]");
        } catch (e) {
            rawRecords = [];
        }

        function parseRecord(r) {
            const date = parseRecordDate(r.created_at || (r.A && r.B ? r.A + " " + r.B : ""));

            // Parse blood pressure
            let sys = Number(r.systolic || 0);
            let dia = Number(r.diastolic || 0);
            if ((!sys || !dia) && (r.G || r.blood_pressure || r.bp_str)) {
                const bpStr = String(r.G || r.blood_pressure || r.bp_str);
                if (bpStr.includes("/")) {
                    const parts = bpStr.split("/");
                    sys = Number(parts[0]) || 0;
                    dia = Number(parts[1]) || 0;
                }
            }

            const hr = Number(r.heart_rate || r.H || 0);
            const spo2 = Number(r.oxygen_saturation || r.I || 0);
            const temp = Number(r.temperature || r.J || 0);
            const bmi = Number(r.bmi || r.M || 0);
            const weight = Number(r.weight || r.K || 0);
            const height = Number(r.height || r.L || 0);

            const patientName = r.patient_name || (r.C && r.D ? (r.C + " " + r.D).trim() : "Patient");
            const patientId = r.patient_id ? String(r.patient_id) : "";

            return {
                raw: r,
                date: date,
                patientName: patientName,
                patientId: patientId,
                systolic: sys,
                diastolic: dia,
                bpStr: sys && dia ? `${sys}/${dia}` : (r.G || "—"),
                bpCategory: r.bp_category || (sys >= 140 || dia >= 90 ? "Stage 2 High BP" : (sys >= 130 || dia >= 80 ? "Stage 1 Elevated" : (sys < 90 ? "Low BP" : "Optimal"))),
                heartRate: hr,
                hrCategory: r.hr_category || (hr > 100 ? "Tachycardia" : (hr < 60 && hr > 0 ? "Bradycardia" : "Normal")),
                oxygenSaturation: spo2,
                spo2Category: r.spo2_category || (spo2 >= 95 ? "Normal" : "Low SpO2"),
                temperature: temp,
                tempCategory: r.temp_category || (temp > 37.5 ? "Elevated / Fever" : (temp < 36.0 && temp > 0 ? "Below Normal" : "Normal")),
                bmi: bmi,
                bmiCategory: r.bmi_category || (bmi < 18.5 ? "Underweight" : (bmi < 25 ? "Normal" : (bmi < 30 ? "Overweight" : "Obese"))),
                weight: weight,
                height: height,
                status: r.status || "Normal"
            };
        }

        function getPreparedRecords() {
            try {
                rawRecords = JSON.parse(container.getAttribute("data-records") || "[]");
            } catch (e) {
                rawRecords = [];
            }

            return rawRecords
                .map(parseRecord)
                .filter(function (r) {
                    return r.date !== null;
                })
                .sort(function (a, b) {
                    return a.date - b.date;
                });
        }

        function filterRecords() {
            let records = getPreparedRecords();

            // Patient filter
            if (patientFilter && patientFilter.value && patientFilter.value !== "all") {
                const targetPid = String(patientFilter.value);
                records = records.filter(function (r) {
                    return r.patientId === targetPid || r.patientName.toLowerCase() === targetPid.toLowerCase();
                });
            }

            // Range filter
            const range = chartRange ? chartRange.value : "all";
            const now = new Date();

            if (range === "daily") {
                const start = new Date(now);
                start.setHours(0, 0, 0, 0);
                const end = getEndOfDay(now);
                records = records.filter(function (r) {
                    return r.date >= start && r.date <= end;
                });
            } else if (range === "weekly") {
                const start = getStartOfWeek(now);
                const end = new Date(start);
                end.setDate(start.getDate() + 7);
                records = records.filter(function (r) {
                    return r.date >= start && r.date < end;
                });
            } else if (range === "monthly") {
                records = records.filter(function (r) {
                    return r.date.getFullYear() === now.getFullYear() && r.date.getMonth() === now.getMonth();
                });
            } else if (range === "yearly") {
                records = records.filter(function (r) {
                    return r.date.getFullYear() === now.getFullYear();
                });
            } else if (range === "custom") {
                const start = getDateFromInput(startDateInput ? startDateInput.value : "", false);
                const end = getDateFromInput(endDateInput ? endDateInput.value : "", true);
                if (start && end) {
                    records = records.filter(function (r) {
                        return r.date >= start && r.date <= end;
                    });
                }
            }

            // Metric valid filter
            if (activeMetric === "bp") {
                return records.filter(function (r) { return r.systolic > 0 && r.diastolic > 0; });
            } else if (activeMetric === "hr") {
                return records.filter(function (r) { return r.heartRate > 0; });
            } else if (activeMetric === "spo2") {
                return records.filter(function (r) { return r.oxygenSaturation > 0; });
            } else if (activeMetric === "temp") {
                return records.filter(function (r) { return r.temperature > 0; });
            } else if (activeMetric === "weight") {
                return records.filter(function (r) { return r.weight > 0; });
            } else { // bmi
                return records.filter(function (r) { return r.bmi > 0; });
            }
        }

        function updateLegend() {
            if (!legendContainer) return;

            if (activeMetric === "bp") {
                legendContainer.innerHTML = `
                    <span><i class="legend-color-dot" style="background:#ef4444;"></i> Systolic (mmHg)</span>
                    <span><i class="legend-color-dot" style="background:#0284c7;"></i> Diastolic (mmHg)</span>
                    <span><i class="legend-ref-line" style="border-color:#10b981;"></i> Normal Target (&lt;120/&lt;80)</span>
                    <span><i class="legend-ref-line" style="border-color:#ef4444;"></i> Hypertension (&ge;140/&ge;90)</span>
                `;
            } else if (activeMetric === "hr") {
                legendContainer.innerHTML = `
                    <span><i class="legend-color-dot" style="background:#8b5cf6;"></i> Pulse Rate (BPM)</span>
                    <span><i class="legend-zone-box" style="background:rgba(139, 92, 246, 0.15);"></i> Normal Resting Zone (60 - 100)</span>
                    <span><i class="legend-ref-line" style="border-color:#f59e0b;"></i> Tachycardia Threshold (&gt;100)</span>
                `;
            } else if (activeMetric === "spo2") {
                legendContainer.innerHTML = `
                    <span><i class="legend-color-dot" style="background:#06b6d4;"></i> SpO2 Saturation (%)</span>
                    <span><i class="legend-ref-line" style="border-color:#10b981;"></i> Optimal Target (&ge;95%)</span>
                    <span><i class="legend-ref-line" style="border-color:#dc2626;"></i> Hypoxia Alert (&lt;95%)</span>
                `;
            } else if (activeMetric === "temp") {
                legendContainer.innerHTML = `
                    <span><i class="legend-color-dot" style="background:#f59e0b;"></i> Body Temp (&deg;C)</span>
                    <span><i class="legend-zone-box" style="background:rgba(245, 158, 11, 0.15);"></i> Normal Range (36.0 - 37.5&deg;C)</span>
                    <span><i class="legend-ref-line" style="border-color:#dc2626;"></i> Fever Line (37.5&deg;C)</span>
                `;
            } else { // bmi
                legendContainer.innerHTML = `
                    <span><i class="legend-color-dot" style="background:#f59e0b;"></i> Below Normal (&lt;18.5)</span>
                    <span><i class="legend-color-dot" style="background:#10b981;"></i> Normal (18.5 - 24.9)</span>
                    <span><i class="legend-color-dot" style="background:#f97316;"></i> Overweight (25 - 29.9)</span>
                    <span><i class="legend-color-dot" style="background:#dc2626;"></i> Obese (&ge;30)</span>
                `;
            }
        }

        function updateStatStrip(records) {
            if (!statAvgEl && !statTargetEl && !statMinEl && !statMaxEl && !statCountEl) return;

            const count = records.length;
            if (statCountEl) statCountEl.textContent = count;

            if (count === 0) {
                if (statAvgEl) statAvgEl.textContent = "—";
                if (statTargetEl) statTargetEl.textContent = "—";
                if (statMinEl) statMinEl.textContent = "—";
                if (statMaxEl) statMaxEl.textContent = "—";
                return;
            }

            if (activeMetric === "bp") {
                const sysVals = records.map(function (r) { return r.systolic; });
                const diaVals = records.map(function (r) { return r.diastolic; });
                const avgSys = Math.round(sysVals.reduce(function (a, b) { return a + b; }, 0) / count);
                const avgDia = Math.round(diaVals.reduce(function (a, b) { return a + b; }, 0) / count);
                const normalCount = records.filter(function (r) { return r.systolic < 120 && r.diastolic < 80; }).length;

                if (statAvgEl) statAvgEl.textContent = `${avgSys}/${avgDia} mmHg`;
                if (statTargetEl) statTargetEl.textContent = `${Math.round((normalCount / count) * 100)}% Optimal`;
                if (statMinEl) statMinEl.textContent = `${Math.min(...sysVals)}/${Math.min(...diaVals)}`;
                if (statMaxEl) statMaxEl.textContent = `${Math.max(...sysVals)}/${Math.max(...diaVals)}`;
            } else if (activeMetric === "hr") {
                const vals = records.map(function (r) { return r.heartRate; });
                const avg = Math.round(vals.reduce(function (a, b) { return a + b; }, 0) / count);
                const normalCount = records.filter(function (r) { return r.heartRate >= 60 && r.heartRate <= 100; }).length;

                if (statAvgEl) statAvgEl.textContent = `${avg} BPM`;
                if (statTargetEl) statTargetEl.textContent = `${Math.round((normalCount / count) * 100)}% Normal`;
                if (statMinEl) statMinEl.textContent = `${Math.min(...vals)} BPM`;
                if (statMaxEl) statMaxEl.textContent = `${Math.max(...vals)} BPM`;
            } else if (activeMetric === "spo2") {
                const vals = records.map(function (r) { return r.oxygenSaturation; });
                const avg = (vals.reduce(function (a, b) { return a + b; }, 0) / count).toFixed(1);
                const normalCount = records.filter(function (r) { return r.oxygenSaturation >= 95; }).length;

                if (statAvgEl) statAvgEl.textContent = `${avg}%`;
                if (statTargetEl) statTargetEl.textContent = `${Math.round((normalCount / count) * 100)}% Normal`;
                if (statMinEl) statMinEl.textContent = `${Math.min(...vals)}%`;
                if (statMaxEl) statMaxEl.textContent = `${Math.max(...vals)}%`;
            } else if (activeMetric === "temp") {
                const vals = records.map(function (r) { return r.temperature; });
                const avg = (vals.reduce(function (a, b) { return a + b; }, 0) / count).toFixed(1);
                const normalCount = records.filter(function (r) { return r.temperature >= 36.0 && r.temperature <= 37.5; }).length;

                if (statAvgEl) statAvgEl.textContent = `${avg} °C`;
                if (statTargetEl) statTargetEl.textContent = `${Math.round((normalCount / count) * 100)}% Normal`;
                if (statMinEl) statMinEl.textContent = `${Math.min(...vals).toFixed(1)} °C`;
                if (statMaxEl) statMaxEl.textContent = `${Math.max(...vals).toFixed(1)} °C`;
            } else { // bmi
                const vals = records.map(function (r) { return r.bmi; });
                const avg = (vals.reduce(function (a, b) { return a + b; }, 0) / count).toFixed(1);
                const normalCount = records.filter(function (r) { return r.bmi >= 18.5 && r.bmi < 25; }).length;

                if (statAvgEl) statAvgEl.textContent = `${avg} kg/m²`;
                if (statTargetEl) statTargetEl.textContent = `${Math.round((normalCount / count) * 100)}% Normal`;
                if (statMinEl) statMinEl.textContent = `${Math.min(...vals).toFixed(1)}`;
                if (statMaxEl) statMaxEl.textContent = `${Math.max(...vals).toFixed(1)}`;
            }
        }

        function renderChart() {
            const records = filterRecords();
            updateLegend();
            updateStatStrip(records);

            const width = 880;
            const height = 340;
            const paddingLeft = 68;
            const paddingRight = 36;
            const paddingTop = 32;
            const paddingBottom = 60;

            const chartWidth = width - paddingLeft - paddingRight;
            const chartHeight = height - paddingTop - paddingBottom;

            // Calculate min and max Y for the active metric
            let minY = 0;
            let maxY = 100;
            let referenceLines = [];
            let shadedZones = [];

            if (activeMetric === "bp") {
                const sysList = records.map(function (r) { return r.systolic; });
                const diaList = records.map(function (r) { return r.diastolic; });
                const allVals = [...sysList, ...diaList];

                minY = allVals.length ? Math.max(40, Math.floor(Math.min(...allVals, 60) - 10)) : 50;
                maxY = allVals.length ? Math.min(220, Math.ceil(Math.max(...allVals, 150) + 15)) : 180;

                // Thresholds
                referenceLines = [
                    { value: 140, label: "140 (Hypertension)", color: "#ef4444", dash: "5,4" },
                    { value: 120, label: "120 (Optimal Sys)", color: "#10b981", dash: "4,4" },
                    { value: 80, label: "80 (Optimal Dia)", color: "#0284c7", dash: "4,4" }
                ];
            } else if (activeMetric === "hr") {
                const vals = records.map(function (r) { return r.heartRate; });
                minY = vals.length ? Math.max(30, Math.floor(Math.min(...vals, 55) - 10)) : 40;
                maxY = vals.length ? Math.min(200, Math.ceil(Math.max(...vals, 110) + 15)) : 140;

                referenceLines = [
                    { value: 100, label: "100 (Tachycardia)", color: "#f59e0b", dash: "5,4" },
                    { value: 60, label: "60 (Bradycardia)", color: "#0284c7", dash: "4,4" }
                ];

                shadedZones = [
                    { yMin: 60, yMax: 100, color: "rgba(139, 92, 246, 0.08)" }
                ];
            } else if (activeMetric === "spo2") {
                const vals = records.map(function (r) { return r.oxygenSaturation; });
                minY = vals.length ? Math.max(75, Math.floor(Math.min(...vals, 92) - 3)) : 88;
                maxY = 101;

                referenceLines = [
                    { value: 95, label: "95% (Clinical Target)", color: "#10b981", dash: "4,4" },
                    { value: 90, label: "90% (Hypoxia Alert)", color: "#dc2626", dash: "5,4" }
                ];

                shadedZones = [
                    { yMin: 95, yMax: 100, color: "rgba(6, 182, 212, 0.08)" }
                ];
            } else if (activeMetric === "temp") {
                const vals = records.map(function (r) { return r.temperature; });
                minY = vals.length ? Math.max(34.0, Number((Math.min(...vals, 35.8) - 0.5).toFixed(1))) : 35.0;
                maxY = vals.length ? Math.min(42.0, Number((Math.max(...vals, 38.0) + 0.5).toFixed(1))) : 39.5;

                referenceLines = [
                    { value: 37.5, label: "37.5°C (Fever Alert)", color: "#dc2626", dash: "5,4" },
                    { value: 36.0, label: "36.0°C (Baseline)", color: "#0284c7", dash: "4,4" }
                ];

                shadedZones = [
                    { yMin: 36.0, yMax: 37.5, color: "rgba(245, 158, 11, 0.08)" }
                ];
            } else { // bmi
                const vals = records.map(function (r) { return r.bmi; });
                minY = vals.length ? Math.max(12, Math.floor(Math.min(...vals, 17) - 2)) : 15;
                maxY = vals.length ? Math.min(50, Math.ceil(Math.max(...vals, 32) + 2)) : 35;

                referenceLines = [
                    { value: 18.5, label: "18.5 (Underweight)", color: "#f59e0b", dash: "4,4" },
                    { value: 25.0, label: "25.0 (Overweight)", color: "#f97316", dash: "4,4" },
                    { value: 30.0, label: "30.0 (Obese)", color: "#dc2626", dash: "5,4" }
                ];

                shadedZones = [
                    { yMin: 18.5, yMax: 24.9, color: "rgba(16, 185, 129, 0.08)" }
                ];
            }

            function getX(index) {
                if (records.length <= 1) return paddingLeft + chartWidth / 2;
                return paddingLeft + (index / (records.length - 1)) * chartWidth;
            }

            function getY(val) {
                if (maxY <= minY) return paddingTop + chartHeight / 2;
                const ratio = (val - minY) / (maxY - minY);
                return paddingTop + chartHeight - ratio * chartHeight;
            }

            let svg = "";

            // Defs for gradients & shadow filters
            svg += `
                <defs>
                    <linearGradient id="sysGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#ef4444" stop-opacity="0.28" />
                        <stop offset="100%" stop-color="#ef4444" stop-opacity="0.0" />
                    </linearGradient>
                    <linearGradient id="diaGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#0284c7" stop-opacity="0.22" />
                        <stop offset="100%" stop-color="#0284c7" stop-opacity="0.0" />
                    </linearGradient>
                    <linearGradient id="primaryGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stop-color="#8b5cf6" stop-opacity="0.25" />
                        <stop offset="100%" stop-color="#8b5cf6" stop-opacity="0.0" />
                    </linearGradient>
                    <filter id="pointGlow" x="-30%" y="-30%" width="160%" height="160%">
                        <feDropShadow dx="0" dy="2" stdDeviation="2.5" flood-opacity="0.25" />
                    </filter>
                </defs>
            `;

            // Draw shaded target zones
            shadedZones.forEach(function (zone) {
                const yTop = Math.max(paddingTop, getY(Math.min(zone.yMax, maxY)));
                const yBottom = Math.min(height - paddingBottom, getY(Math.max(zone.yMin, minY)));
                const zoneHeight = yBottom - yTop;
                if (zoneHeight > 0) {
                    svg += `<rect x="${paddingLeft}" y="${yTop}" width="${chartWidth}" height="${zoneHeight}" fill="${zone.color}" rx="4" />`;
                }
            });

            // Grid lines and Y axis ticks
            const ySteps = 5;
            const stepVal = (maxY - minY) / ySteps;
            for (let i = 0; i <= ySteps; i++) {
                const val = activeMetric === "temp" ? (minY + stepVal * i).toFixed(1) : Math.round(minY + stepVal * i);
                const y = getY(val);

                svg += `
                    <line x1="${paddingLeft}" y1="${y}" x2="${width - paddingRight}" y2="${y}" stroke="#e5edfa" stroke-width="1" stroke-dasharray="3,3" />
                    <text x="${paddingLeft - 12}" y="${y + 4}" fill="#718096" font-size="11" font-weight="500" text-anchor="end">${val}</text>
                `;
            }

            // Reference threshold lines
            referenceLines.forEach(function (ref) {
                if (ref.value >= minY && ref.value <= maxY) {
                    const y = getY(ref.value);
                    svg += `
                        <line x1="${paddingLeft}" y1="${y}" x2="${width - paddingRight}" y2="${y}" stroke="${ref.color}" stroke-width="1.4" stroke-dasharray="${ref.dash}" />
                        <text x="${width - paddingRight - 6}" y="${y - 5}" fill="${ref.color}" font-size="10" font-weight="600" text-anchor="end">${ref.label}</text>
                    `;
                }
            });

            // Main X & Y axes
            svg += `
                <line x1="${paddingLeft}" y1="${paddingTop}" x2="${paddingLeft}" y2="${height - paddingBottom}" stroke="#cbd5e1" stroke-width="1.5" />
                <line x1="${paddingLeft}" y1="${height - paddingBottom}" x2="${width - paddingRight}" y2="${height - paddingBottom}" stroke="#cbd5e1" stroke-width="1.5" />
            `;

            // X axis labels
            records.forEach(function (r, idx) {
                const x = getX(idx);
                const rangeVal = chartRange ? chartRange.value : "all";
                let xLabel = formatShortDate(r.date);

                if (rangeVal === "daily") {
                    xLabel = r.date.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
                }

                const showLabel =
                    records.length <= 10 ||
                    idx === 0 ||
                    idx === records.length - 1 ||
                    idx % Math.ceil(records.length / 7) === 0;

                if (showLabel) {
                    svg += `
                        <line x1="${x}" y1="${height - paddingBottom}" x2="${x}" y2="${height - paddingBottom + 5}" stroke="#94a3b8" stroke-width="1" />
                        <text x="${x}" y="${height - paddingBottom + 20}" fill="#64748b" font-size="10.5" font-weight="500" text-anchor="middle">${xLabel}</text>
                    `;
                }
            });

            // Draw line plots
            if (activeMetric === "bp") {
                // Dual lines: Systolic (red/coral) & Diastolic (blue)
                if (records.length > 1) {
                    // Systolic Area fill
                    let sysAreaPath = `M ${getX(0)} ${getY(records[0].systolic)}`;
                    for (let i = 1; i < records.length; i++) {
                        sysAreaPath += ` L ${getX(i)} ${getY(records[i].systolic)}`;
                    }
                    sysAreaPath += ` L ${getX(records.length - 1)} ${height - paddingBottom} L ${getX(0)} ${height - paddingBottom} Z`;
                    svg += `<path d="${sysAreaPath}" fill="url(#sysGradient)" />`;

                    // Diastolic Area fill
                    let diaAreaPath = `M ${getX(0)} ${getY(records[0].diastolic)}`;
                    for (let i = 1; i < records.length; i++) {
                        diaAreaPath += ` L ${getX(i)} ${getY(records[i].diastolic)}`;
                    }
                    diaAreaPath += ` L ${getX(records.length - 1)} ${height - paddingBottom} L ${getX(0)} ${height - paddingBottom} Z`;
                    svg += `<path d="${diaAreaPath}" fill="url(#diaGradient)" />`;

                    // Systolic stroke line
                    let sysLinePath = `M ${getX(0)} ${getY(records[0].systolic)}`;
                    for (let i = 1; i < records.length; i++) {
                        sysLinePath += ` L ${getX(i)} ${getY(records[i].systolic)}`;
                    }
                    svg += `<path d="${sysLinePath}" fill="none" stroke="#ef4444" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />`;

                    // Diastolic stroke line
                    let diaLinePath = `M ${getX(0)} ${getY(records[0].diastolic)}`;
                    for (let i = 1; i < records.length; i++) {
                        diaLinePath += ` L ${getX(i)} ${getY(records[i].diastolic)}`;
                    }
                    svg += `<path d="${diaLinePath}" fill="none" stroke="#0284c7" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />`;
                }

                // Points & interactivity
                records.forEach(function (r, idx) {
                    const x = getX(idx);
                    const ySys = getY(r.systolic);
                    const yDia = getY(r.diastolic);

                    // Systolic point
                    svg += `
                        <circle cx="${x}" cy="${ySys}" r="5.2" fill="#ef4444" stroke="#ffffff" stroke-width="2" class="vitals-chart-point" filter="url(#pointGlow)"
                            data-patient="${escapeHtml(r.patientName)}"
                            data-date="${escapeHtml(formatDateTime(r.date))}"
                            data-value="Systolic: ${r.systolic} mmHg | Diastolic: ${r.diastolic} mmHg (BP: ${r.bpStr})"
                            data-cat="${escapeHtml(r.bpCategory)}">
                            <title>${r.patientName} (${formatDateTime(r.date)}): BP ${r.bpStr} mmHg [${r.bpCategory}]</title>
                        </circle>
                    `;

                    // Diastolic point
                    svg += `
                        <circle cx="${x}" cy="${yDia}" r="5.2" fill="#0284c7" stroke="#ffffff" stroke-width="2" class="vitals-chart-point" filter="url(#pointGlow)"
                            data-patient="${escapeHtml(r.patientName)}"
                            data-date="${escapeHtml(formatDateTime(r.date))}"
                            data-value="Diastolic: ${r.diastolic} mmHg (BP: ${r.bpStr})"
                            data-cat="${escapeHtml(r.bpCategory)}">
                            <title>${r.patientName} (${formatDateTime(r.date)}): BP ${r.bpStr} mmHg [${r.bpCategory}]</title>
                        </circle>
                    `;

                    // Value label on hover or if sparse
                    if (records.length <= 12) {
                        svg += `<text x="${x}" y="${ySys - 9}" fill="#b91c1c" font-size="9.5" font-weight="700" text-anchor="middle">${r.systolic}</text>`;
                        svg += `<text x="${x}" y="${yDia + 16}" fill="#0369a1" font-size="9.5" font-weight="700" text-anchor="middle">${r.diastolic}</text>`;
                    }
                });
            } else {
                // Single line metrics: hr, spo2, temp, bmi, weight
                let lineColor = "#8b5cf6";
                let unit = "BPM";
                if (activeMetric === "spo2") { lineColor = "#06b6d4"; unit = "%"; }
                else if (activeMetric === "temp") { lineColor = "#f59e0b"; unit = "°C"; }
                else if (activeMetric === "bmi") { lineColor = "#10b981"; unit = "kg/m²"; }
                else if (activeMetric === "weight") { lineColor = "#3b82f6"; unit = "kg"; }

                function getMetricVal(r) {
                    if (activeMetric === "hr") return r.heartRate;
                    if (activeMetric === "spo2") return r.oxygenSaturation;
                    if (activeMetric === "temp") return r.temperature;
                    if (activeMetric === "weight") return r.weight;
                    return r.bmi;
                }

                function getMetricCategory(r) {
                    if (activeMetric === "hr") return r.hrCategory;
                    if (activeMetric === "spo2") return r.spo2Category;
                    if (activeMetric === "temp") return r.tempCategory;
                    if (activeMetric === "weight") return `${r.weight} kg`;
                    return r.bmiCategory;
                }

                function getPointColor(val) {
                    if (activeMetric === "bmi") {
                        if (val < 18.5) return "#f59e0b";
                        if (val < 25) return "#10b981";
                        if (val < 30) return "#f97316";
                        return "#dc2626";
                    }
                    if (activeMetric === "hr") {
                        if (val > 100) return "#f59e0b";
                        if (val < 60) return "#0284c7";
                        return "#10b981";
                    }
                    if (activeMetric === "spo2") {
                        return val >= 95 ? "#06b6d4" : "#dc2626";
                    }
                    if (activeMetric === "temp") {
                        if (val > 37.5) return "#dc2626";
                        if (val < 36.0) return "#0284c7";
                        return "#10b981";
                    }
                    return lineColor;
                }

                if (records.length > 1) {
                    let areaPath = `M ${getX(0)} ${getY(getMetricVal(records[0]))}`;
                    for (let i = 1; i < records.length; i++) {
                        areaPath += ` L ${getX(i)} ${getY(getMetricVal(records[i]))}`;
                    }
                    areaPath += ` L ${getX(records.length - 1)} ${height - paddingBottom} L ${getX(0)} ${height - paddingBottom} Z`;
                    svg += `<path d="${areaPath}" fill="url(#primaryGradient)" />`;

                    let linePath = `M ${getX(0)} ${getY(getMetricVal(records[0]))}`;
                    for (let i = 1; i < records.length; i++) {
                        linePath += ` L ${getX(i)} ${getY(getMetricVal(records[i]))}`;
                    }
                    svg += `<path d="${linePath}" fill="none" stroke="${lineColor}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />`;
                }

                records.forEach(function (r, idx) {
                    const val = getMetricVal(r);
                    const x = getX(idx);
                    const y = getY(val);
                    const pointColor = getPointColor(val);
                    const catLabel = getMetricCategory(r);

                    svg += `
                        <circle cx="${x}" cy="${y}" r="5.2" fill="${pointColor}" stroke="#ffffff" stroke-width="2" class="vitals-chart-point" filter="url(#pointGlow)"
                            data-patient="${escapeHtml(r.patientName)}"
                            data-date="${escapeHtml(formatDateTime(r.date))}"
                            data-value="${val} ${unit}"
                            data-cat="${escapeHtml(catLabel)}">
                            <title>${r.patientName} (${formatDateTime(r.date)}): ${val} ${unit} [${catLabel}]</title>
                        </circle>
                    `;

                    if (records.length <= 16) {
                        svg += `<text x="${x}" y="${y - 9}" fill="#334155" font-size="9.5" font-weight="700" text-anchor="middle">${val}</text>`;
                    }
                });
            }

            // Empty state notice
            if (records.length === 0) {
                svg += `
                    <text x="${width / 2}" y="${height / 2}" fill="#64748b" font-size="14" font-weight="500" text-anchor="middle">
                        No health records available for the selected filters.
                    </text>
                `;
            }

            chartSvg.innerHTML = svg;

            // Wire up interactive floating tooltip
            wirePointTooltips(chartSvg);

            // Update description note
            if (chartNote) {
                const metricNames = {
                    bp: "Blood Pressure (Systolic & Diastolic)",
                    hr: "Heart Rate / Resting Pulse",
                    spo2: "Oxygen Saturation (SpO2)",
                    temp: "Body Temperature",
                    bmi: "Body Mass Index (BMI)",
                    weight: "Body Weight"
                };
                const mName = metricNames[activeMetric] || activeMetric.toUpperCase();
                const rangeName = chartRange ? chartRange.options[chartRange.selectedIndex].text : "All Time";
                chartNote.textContent = `${rangeName}: Showing ${records.length} records for ${mName}.`;
            }
        }

        function escapeHtml(str) {
            if (!str) return "";
            return String(str)
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        function wirePointTooltips(svgEl) {
            const points = svgEl.querySelectorAll(".vitals-chart-point");
            points.forEach(function (pt) {
                pt.addEventListener("mouseenter", function (e) {
                    const patient = pt.getAttribute("data-patient");
                    const date = pt.getAttribute("data-date");
                    const value = pt.getAttribute("data-value");
                    const cat = pt.getAttribute("data-cat");

                    chartTooltip.innerHTML = `
                        <div class="vtooltip-header">
                            <strong>${patient}</strong>
                            <span>${date}</span>
                        </div>
                        <div class="vtooltip-value">${value}</div>
                        ${cat ? `<div class="vtooltip-badge">${cat}</div>` : ""}
                    `;

                    chartTooltip.style.display = "block";
                    positionTooltip(e);
                });

                pt.addEventListener("mousemove", function (e) {
                    positionTooltip(e);
                });

                pt.addEventListener("mouseleave", function () {
                    chartTooltip.style.display = "none";
                });
            });
        }

        function positionTooltip(e) {
            const tooltipWidth = chartTooltip.offsetWidth || 180;
            const tooltipHeight = chartTooltip.offsetHeight || 70;
            let left = e.pageX + 14;
            let top = e.pageY - tooltipHeight - 10;

            if (left + tooltipWidth > window.innerWidth - 10) {
                left = e.pageX - tooltipWidth - 14;
            }
            if (top < 10) {
                top = e.pageY + 14;
            }

            chartTooltip.style.left = left + "px";
            chartTooltip.style.top = top + "px";
        }

        // Toggle custom date range inputs visibility
        function toggleCustomRange() {
            if (!customRangeBox) return;
            if (chartRange && chartRange.value === "custom") {
                customRangeBox.classList.remove("hidden");
                customRangeBox.style.display = "flex";
            } else {
                customRangeBox.classList.add("hidden");
                customRangeBox.style.display = "none";
            }
        }

        // Event Listeners for metric tabs
        metricTabs.forEach(function (tab) {
            tab.addEventListener("click", function () {
                metricTabs.forEach(function (t) { t.classList.remove("active"); });
                tab.classList.add("active");
                activeMetric = tab.getAttribute("data-metric");
                if (metricSelect) metricSelect.value = activeMetric;
                renderChart();
            });
        });

        if (metricSelect) {
            metricSelect.addEventListener("change", function () {
                activeMetric = metricSelect.value;
                metricTabs.forEach(function (tab) {
                    if (tab.getAttribute("data-metric") === activeMetric) {
                        tab.classList.add("active");
                    } else {
                        tab.classList.remove("active");
                    }
                });
                renderChart();
            });
        }

        if (chartRange) {
            chartRange.addEventListener("change", function () {
                toggleCustomRange();
                renderChart();
            });
        }

        if (patientFilter) {
            patientFilter.addEventListener("change", renderChart);
        }

        if (startDateInput) {
            startDateInput.addEventListener("change", renderChart);
        }

        if (endDateInput) {
            endDateInput.addEventListener("change", renderChart);
        }

        toggleCustomRange();
        renderChart();

        // Listen for live refresh updates
        container.addEventListener("recordsUpdated", function () {
            renderChart();
        });
    }
});