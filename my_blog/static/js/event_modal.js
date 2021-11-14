	document.addEventListener('DOMContentLoaded', function() {
		var calendarEl = document.getElementById('calendar');
		
		var calendar = new FullCalendar.Calendar(calendarEl, {
			initialView: 'dayGridMonth',
			headerToolbar: {
				left: 'prev,next today',
				center: 'title',
				right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
			},
			height: 'auto',
			navLinks: true, // can click day/week names to navigate views
			editable: true,
			dayMaxEvents: true,
			selectable: true,
			selectMirror: true,
			nowIndicator: true,
			
			
			eventClick: function(arg) {
				
				{% if user.is_superuser %}
				var token = '{{csrf_token}}';
				if (confirm('Are you sure you want to delete this event?')) {
					$.ajax({
						url: URL,
						type: 'POST',
						headers:{
							"X-CSRFToken": token
						},
						data: {'id':arg.event.id},
						success: function () {
							arg.event.remove()
						}
					});
				}
				
				{% else %}
					var eventObj = arg.event;
					alert('Title: ' + eventObj.title + '\nStart: ' + eventObj.start  + '\nDescription: ' + eventObj.extendedProps.description );
					{% endif %}	
				},
				events: [
					{% for event in events %}
					{
						id    : '{{ event.id }}',
						title : '{{ event.title }}',
						start : '{{ event.start_time|date:'c' }}',
						end   : '{{ event.end_time|date:'c' }}',
						description: '{{ event.description }}'
					},
					{% endfor %}
					
				],
				
			});
			
		calendar.render();
		var frm = $('#AddEventForm');
		frm.on('submit', function(event){
			event.preventDefault();
			console.log("form submitted!")  // sanity check
			add_event();
		});
		// AJAX for posting
		function add_event() {
			console.log("event adding is working!") // sanity check
			$.ajax({
				url : frm.attr('action'),// the endpoint
				type : frm.attr('method'),// http method
				data : frm.serialize(), // data sent with the post request
				// handle a successful response
				success : function(response) {
					frm[0].reset();
					console.log(response);
					calendar.addEvent(response);
					console.log('success');
				},
				// handle a non-successful response
				error : function(xhr,errmsg,err) {
				}
			});
			return false;
		};
		
	});
