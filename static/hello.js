"use strict"

function teste(){
    console.log($('#nome').val());
    $.ajax({
        url: '/logged',
        data: JSON.stringify({nome:$('#nome').val()}),
        contentType: 'application/json;charset=UTF-8',
        type: 'POST',
        success: function(response) {
           response = JSON.parse(response)
            $('#target').text('Seja bem vindo: '+response.usuario)
        },
        error: function(error) {
            console.log(error);

        }
    });
}

function teste2(){
    console.log($('#nome').val());
    $.ajax({
        url: '/logged_two',
        data: JSON.stringify({nome:$('#nome').val()}),
        contentType: 'application/json;charset=UTF-8',
        type: 'POST',
        success: function(response) {
            $('#target').html(response)
        },
        error: function(error) {
            console.log(error);

        }
    });
}

function upload(){
    let form = $('form').get(0);
    $.ajax({
        url:'/upload',
        data: new FormData(form),
        contentType: false,
        cache: false,
        type: 'POST',
        processData: false,
        async: false,
        success: function(response){
            response = JSON.parse(response);
            console.log(response);
            if(response.url === 'error'){
                location.reload();
                return;
            }
            let item = $("<li />");
            let element = $("<a />", {
                href : response.url,
                text : response.name
            });

            item.append(element);
            $('#uploaded_files').append(item);
        },

        error: function(error){
            console.log(error);
        }
    });
}