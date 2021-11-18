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
    
    let csrfToken = '{{ csrf_token }}'


    if (head && body && id) {
        button.innerText = 'Sending...';
        button.disabled = true;

        const res = await fetch('/send_push/', {
            method: 'POST',
            body: JSON.stringify({head, body, id}),
            credentials : 'include',
            headers: {
                'content-type': 'application/json',
                'X-CSRF-TOKEN': csrfToken
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