$(document).ready(function(){
    const chatForm = $('.chat=form');
    const chatInput = $('input[name = "content"]');
    const chatMessages = $ ('.chat-message');
    if (!chatForm.length) return;
    const sendUrl = chatForm.data('send-url');
    const getUrl = chatForm.data('get-url');

    function escapeHtml(text){
        return $('<div>').text(text).html();
    }
    function renderMessages(messages){
        chatMessages.empty();
        if(!messages.length){
            chatMessages.append('<p class="no-messages">no messages yet, say hi :)');
            return;
        }
        messages,forEach(function(message){
            <div class ="message $ {messageClass}">
                <div class ="message-header">
                    <strong>${escapeHtml(message.sender)}</strong>
                    <span class = "messsage-time">${escapeHtml(message.timestamp)}</span>
                </div>
                <p>${escapeHtml(message.content)}</p>
            </div>
            ;
            chatMessages.append(messageHtml);
        });
        chatMessages.scrollTop(chatMessages[0].scrollHeight);
    }
    function loadMessages(){
        $.get(getUrl, function(data){
            renderMessages(data.messages);
        });
    }
    chatForm.on('submit', function(e){
        e.preventDefault();
        const content = chatInput.val().trim();
        if(!content) return;
        $.post(sendUrl,{
            content: content,
            csrfmiddlewaretoken: $('input[name= "csrfmiddlewaretoken"]').val()
        }, function(data){
            if(data.success){
                chatInput.val('');
                loadMessages();
            }
        });
    });
    loadMessages();
    serInterval(loadMessages, 3000);
});