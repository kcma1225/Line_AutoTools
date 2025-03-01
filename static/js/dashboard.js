function openPopup() {
    document.getElementById("popupForm").classList.remove("hidden");
}

function closePopup(event) {
    document.getElementById("popupForm").classList.add("hidden");
}

function openRecipientPopup() {
    document.getElementById("recipientPopup").classList.remove("hidden");
}

function closeRecipientPopup(event) {
    document.getElementById("recipientPopup").classList.add("hidden");
}

document.getElementById("openPopup").addEventListener("click", openPopup);
document.getElementById("openRecipientPopup").addEventListener("click", openRecipientPopup);


// ------------------------- 訊息內容區塊 ------------------------- 
function addMessage() {
    const messageInput = document.getElementById("messageInput");
    const messageList = document.getElementById("messageList");
    if (messageInput.value.trim() === "") return;

    const listItem = document.createElement("div");
    listItem.classList.add("flex", "justify-between", "items-center", "p-2", "bg-white", "shadow", "rounded-md");

    listItem.innerHTML = `
        <span>${messageList.children.length + 1}. ${messageInput.value}</span>
        <button class="px-2 py-1 bg-red-500 text-white rounded-md hover:bg-red-600" onclick="removeMessage(this)">刪除</button>
    `;
    messageList.appendChild(listItem);
    messageInput.value = "";
}

function removeMessage(button) {
    button.parentElement.remove();
}


// ------------------------- Form submit -------------------------
document.getElementById("submitForm").addEventListener("click", async function() {
    const recipientList = document.querySelectorAll("#recipientList div span");
    const messageTime = document.getElementById("messageTime").value;
    const messageFrequency = document.getElementById("messageFrequency").value;
    const messageList = document.querySelectorAll("#messageList div span");

    if (recipientList.length === 0 || !messageTime || !messageFrequency || messageList.length === 0) {
        alert("請確保所有欄位都已填寫！");
        return;
    }

    const recipients = Array.from(recipientList).map(span => span.innerText);
    const messages = Array.from(messageList).map(span => span.innerText.replace(/^\d+\.\s*/, ''));

    if (isNaN(messageFrequency) || messageFrequency < 0 || !Number.isInteger(Number(messageFrequency))) {
        alert("發訊息週期必須為非負整數");
        return;
    }

    const formData = new FormData();
    formData.append("recipients", JSON.stringify(recipients));
    formData.append("time", messageTime);
    formData.append("frequency", messageFrequency);
    formData.append("messages", JSON.stringify(messages));

    try {
        const response = await fetch("/save-formdata", {
            method: "POST",
            body: formData
        });
        
        const result = await response.json();
        if (result.success) {
            window.location.reload();
            showSuccessMessage("成功新增定時傳訊對象");
            closePopup();
        } else {
            alert("儲存失敗: " + result.error);
        }
    } catch (error) {
        alert("請求發生錯誤，請稍後再試");
        console.error("儲存錯誤:", error);
    }
});

function showSuccessMessage(message) {
    const successDiv = document.createElement("div");
    successDiv.innerText = message;
    successDiv.classList.add("fixed", "top-4", "right-4", "bg-green-500", "text-white", "p-3", "rounded-md", "shadow-lg", "transition", "opacity-100");
    document.body.appendChild(successDiv);
    
    setTimeout(() => {
        successDiv.classList.add("opacity-0");
        setTimeout(() => successDiv.remove(), 500);
    }, 3000);
}


// ------------------------- Search popup input button ------------------------- 
document.getElementById("recipientSearchButton").addEventListener("click", async function() {
    const query = document.getElementById("recipientSearchInput").value.trim();
    const resultsContainer = document.getElementById("recipientSearchResults");
    resultsContainer.innerHTML = "";

    if (query.length === 0) {
        resultsContainer.innerHTML = "<p class='text-gray-500 text-center'>請輸入搜尋關鍵字</p>";
        return;
    }

    resultsContainer.innerHTML = `
        <div class='flex justify-center items-center py-4'>
            <div class='animate-spin rounded-full h-10 w-10 border-b-2 border-gray-900'></div>
        </div>
    `;

    try {
        const formData = new FormData();
        formData.append("target_name", query);

        const response = await fetch("/search-target", {
            method: "POST",
            body: formData
        });

        const result = await response.json();
        resultsContainer.innerHTML = "";

        if (!result.success) {
            resultsContainer.innerHTML = "<p class='text-red-500 text-center'>搜尋失敗，請重試</p>";
            return;
        }

        const { groups, friends } = result.data;
        if (groups.length === 0 && friends.length === 0) {
            resultsContainer.innerHTML = "<p class='text-gray-500 text-center'>無搜尋結果</p>";
            return;
        }

        function createListSection(title, data, type) {
            const sectionHeader = document.createElement("h3");
            sectionHeader.classList.add("text-lg", "font-bold", "mt-2", "text-blue-600");
            sectionHeader.innerText = title;
            resultsContainer.appendChild(sectionHeader);

            data.forEach(entry => {
                const item = document.createElement("div");
                item.classList.add("p-2", "bg-white", "rounded-md", "shadow", "cursor-pointer", "hover:bg-gray-100", "border", "border-gray-300", "text-center", "m-1");
                item.innerHTML = `<span>${entry[`${type}_name`]}</span>`;
                item.addEventListener("click", () => toggleSelection(item, entry[`${type}_name`]));
                resultsContainer.appendChild(item);
            });
        }

        if (groups.length > 0) createListSection("群組", groups, "g");
        if (friends.length > 0) createListSection("好友", friends, "f");

    } catch (error) {
        console.error("搜尋錯誤:", error);
        resultsContainer.innerHTML = "<p class='text-red-500 text-center'>發生錯誤，請稍後再試</p>";
    }
});

const selectedRecipients = new Set();

function toggleSelection(item, name) {
    if (!selectedRecipients.has(name)) {
        selectedRecipients.add(name);
        item.classList.add("bg-green-200");
    } else {
        selectedRecipients.delete(name);
        item.classList.remove("bg-green-200");
        item.classList.add("bg-red-200");
        setTimeout(() => item.classList.remove("bg-red-200"), 500);
    }
}


function removeRecipient(button, name) {
    selectedRecipients.delete(name);
    button.parentElement.remove();
}

document.getElementById("confirmSelection").addEventListener("click", () => {
    const recipientList = document.getElementById("recipientList");
    recipientList.innerHTML = "";
    selectedRecipients.forEach(name => {
        const recipientItem = document.createElement("div");
        recipientItem.classList.add("flex", "justify-between", "items-center", "p-1", "bg-gray-200", "rounded-md", "shadow", "m-1");
        recipientItem.innerHTML = `
            <span>${name}</span>
            <button class="px-2 py-1 bg-red-500 text-white rounded-md hover:bg-red-600" onclick="removeRecipient(this, '${name}')">刪除</button>
        `;
        recipientList.appendChild(recipientItem);
    });
    closeRecipientPopup();
});

//------------------------- 顯示已設定的訊息 -------------------------

document.addEventListener("DOMContentLoaded", async function() {
    await loadScheduledMessages();
});

async function loadScheduledMessages() {
    try {
        const response = await fetch("/get-scheduled-messages");
        const result = await response.json();
        if (result.success) {
            const scheduleList = document.getElementById("scheduleList");
            scheduleList.innerHTML = "";
            result.data.forEach(entry => {
                const listItem = document.createElement("li");
                listItem.classList.add("grid", "grid-cols-5", "gap-4", "p-3", "items-center", "text-center");
                listItem.innerHTML = `
                    <div class='hidden' data-id="${entry.id}"></div>
                    <div class="flex items-center justify-center people-icon cursor-pointer">
                        <span class="font-semibold" onclick="showIconPopup('收件人', ${JSON.stringify(entry.name)})">
                            ${entry.name.length > 2 ? '<i class="bi bi-people-fill"></i>' : entry.name.join(", ")}
                        </span>
                    </div>
                    <div class="bg-yellow-200 px-3 py-1 rounded-md font-semibold text-gray-800">${entry.time}</div>
                    <div class="text-gray-700">每 ${entry.period} 天執行一次</div>
                    <div class="cursor-pointer text-blue-500 chat-icon" onclick="showIconPopup('訊息內容', ${JSON.stringify(entry.msg)})">
                        <i class="bi bi-chat-dots-fill"></i>
                    </div>
                    <div class="cursor-pointer text-red-500 delete-icon" onclick="confirmDelete(${entry.id}, this)">
                        <i class="bi bi-trash-fill"></i>
                    </div>
                `;
                scheduleList.appendChild(listItem);
            });
        }
    } catch (error) {
        console.error("載入定時傳訊列表時發生錯誤:", error);
    }
}

function confirmDelete(id, element) {
    if (confirm("確定要刪除此定時傳訊嗎？")) {
        deleteScheduledMessage(id, element);
    }
}

async function deleteScheduledMessage(id, element) {
    try {
        const formData = new FormData();
        formData.append("id", id);
        const response = await fetch("/delete-scheduled-message", {
            method: "POST",
            body: formData
        });
        
        const result = await response.json();
        if (result.success) {
            element.parentElement.remove();
            showDeleteMessage("定時傳訊已成功刪除");
        } else {
            alert("刪除失敗: " + result.error);
        }
    } catch (error) {
        alert("請求發生錯誤，請稍後再試");
        console.error("刪除錯誤:", error);
    }
}

function showIconPopup(title, content) {
    const overlay = document.createElement("div");
    overlay.classList.add("fixed", "top-0", "left-0", "w-full", "h-full", "bg-black", "bg-opacity-50", "flex", "items-center", "justify-center", "z-40");
    
    const popupDiv = document.createElement("div");
    popupDiv.classList.add("bg-white", "shadow-lg", "rounded-lg", "p-4", "w-1/3", "z-50");
    popupDiv.innerHTML = `
        <h3 class="text-lg font-bold mb-2">${title}</h3>
        <div class="text-gray-700">${Array.isArray(content) ? content.join("<br>") : content}</div>
        <button class="mt-4 px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600" onclick="closeIconPopup(this)">關閉</button>
    `;
    
    overlay.appendChild(popupDiv);
    document.body.appendChild(overlay);
}

function closeIconPopup(button) {
    button.parentElement.parentElement.remove();
}

function showDeleteMessage(message) {
    const deleteDiv = document.createElement("div");
    deleteDiv.innerText = message;
    deleteDiv.classList.add("fixed", "top-4", "right-4", "bg-red-500", "text-white", "p-3", "rounded-md", "shadow-lg", "transition", "opacity-100");
    document.body.appendChild(deleteDiv);
    
    setTimeout(() => {
        deleteDiv.classList.add("opacity-0");
        setTimeout(() => deleteDiv.remove(), 500);
    }, 3000);
}