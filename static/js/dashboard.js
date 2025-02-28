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
document.getElementById("submitForm").addEventListener("click", function() {
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

    const formData = {
        recipients,
        time: messageTime,
        frequency: Number(messageFrequency),
        messages
    };

    alert(JSON.stringify(formData, null, 2));
});

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
