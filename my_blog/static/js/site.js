const pushForm = document.getElementById('send-push__form');
const errorMsg = document.querySelector('.error');

pushForm.addEventListener('submit', async function (e) {
    e.preventDefault();
    const input = this[0];
    const textarea = this[1];
    const button = this[2];
    errorMsg.innerText = '';

    const head = input.value;
    const body = textarea.value;
    console.log(head+':'+body);
    const meta = document.querySelector('meta[name="user_id"]');
    const id = meta ? meta.content : null;
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;


    if (head && body && id) {
        button.innerText = 'Sending...';
        button.disabled = true;

        const res = await fetch('/send_push/', {
            method: 'POST',
            mode: 'same-origin',
            body: JSON.stringify({head, body, id}),
            credentials : 'include',
            headers: {
                'content-type': 'application/json',
                'X-CSRF-TOKEN': csrftoken
            }
        });
        if (res.status === 200) {
            console.log(res.status);
            button.innerText = 'Send another 😃!';
            button.disabled = false;
            input.value = '';
            textarea.value = '';
        } else {
            errorMsg.innerText = res.message;
            console.log(res);
            button.innerText = 'Something broke 😢..  Try again?';
            button.disabled = false;
        }
    }
    else {
        let error;
        if (!head || !body){
            error = 'Please ensure you complete the form 🙏🏾'
        }
        else if (!id){
            error = "Are you sure you're logged in? 🤔. Make sure! 👍🏼"
        }
        errorMsg.innerText = error;
    }
});

$(function() {
    
    
    // This function gets cookie with a given name
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');
    
    /*
    The functions below will create a header with csrftoken
    */
    
    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    function sameOrigin(url) {
        // test that a given url is a same-origin URL
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
        (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
        // or any other URL that isn't scheme relative or absolute i.e relative.
        !(/^(\/\/|http:|https:).*/.test(url));
    }
    
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    
});