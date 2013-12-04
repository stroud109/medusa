$(function() {

    console.log('Loading camera.js');

    var videoElem = document.getElementById("videoElem");
    var canvasElem = document.getElementById("canvasFeed");
    // Get our canvas's 2d context
    var context = canvasElem.getContext('2d');

    console.log('Have access to canvases', videoElem, canvasElem);


    var renderTimer = null;

    var drawSingleFrame = function () {
        context.drawImage(videoElem, 0, 0, videoElem.width, videoElem.height);
    };

    var startCapture = function () {
        videoElem.play();
        renderTimer = setInterval(drawSingleFrame, 50);
    };

    var pauseCapture = function () {
        videoElem.pause();
        if (renderTimer) clearInterval(renderTimer);
    };

    var whenUserGrantsAccess = function (mediaStreamObject) {
        console.log('User granted access to camera');
        console.log(mediaStreamObject);

        videoElem.src = window.URL.createObjectURL(mediaStreamObject);

        // Tell the video element to 'play' the stream from the camera
        // videoElem.play();


        // Set our draw context to 'mirror'
        // context.translate(canvasElem.width, 0);
        // context.scale(-1, 1);

        // Start to draw the video into the canvas

        startCapture();
        processCameraImage();
    //     var drawSingleFrame = function () {

    //         context.drawImage(videoElem, 0, 0, videoElem.width, videoElem.height);

    //     };

    //     //
    //     setInterval(drawSingleFrame, 50);
    };

    // Shim the requestAnimationFrame HTML5 API
    // Paul Irish
    // http://www.paulirish.com/2011/requestanimationframe-for-smart-animating/

    // window.requestAnimationFrame = (function(){
    //   return  window.requestAnimationFrame       ||
    //           window.webkitRequestAnimationFrame ||
    //           window.mozRequestAnimationFrame    ||
    //           function( callback ){
    //             window.setTimeout(callback, 1000 / 60);
    //           };
    // })();

    // Shim the getUserMedia HTML5 API
    navigator.getUserMedia = (function () {
        return navigator.getUserMedia       ||
               navigator.webkitGetUserMedia ||
               navigator.mozGetUserMedia    ||
               navigator.msGetUserMedia;
    })();

    var askForCamera = function() {
        console.log("accessing camera, in theory");
        // Check if the browser has a camera
        if (navigator.getUserMedia) {
            // If browser has a camera, ask the user
            // for access to the camera, and when the user
            // grants access, call the `whenUserGrantsAccess` callback.
            navigator.getUserMedia({
                video: true,
                audio: false
            }, whenUserGrantsAccess);
        // If the browser does not have a camera, throw an error
        } else {
            throw new Error('Browser does not appear to support getUserMedia');
        }
    };

    // console.log('If\'m doing other shit');
    var Camera = {
        askForCamera: askForCamera,
        startCapture: startCapture,
        pauseCapture: pauseCapture,
        drawSingleFrame: drawSingleFrame
    };

    var messageContainer = $(".flash-messages");

    var flashMessage = function(alertLevel, message){
        var messageElem = $("<div class='alert alert-"+ alertLevel +"'>"+ message +"<br/></div>");
        messageContainer.html(messageElem);
        // messageElem.fadeOut(2000)
    };

    Camera.askForCamera();


    // Javascripts from search.html file
    // *********************************

    function receiveMessage(e) {
        console.log(e.data);
        if (!(e.data.success || isCancelled)) {
            setTimeout(processCameraImage, 50);
        }
        if (e.data.success) {
            Camera.pauseCapture();
            var ean = e.data.result[0];
            document.location="/results?ean="+ean.replace("EAN-13: ", "");
        }
        // if(e.data.success === "log") {
        //     console.log(e.data.result);
        //     return;
        // }
        // workerCount--;
        // if(e.data.success){
        //     var tempArray = e.data.result;
        //     for(var i = 0; i < tempArray.length; i++) {
        //         if(resultArray.indexOf(tempArray[i]) == -1) {
        //             resultArray.push(tempArray[i]);
        //         }
        //     }
        //     Result.innerHTML=resultArray.join("<br />");
        // }else{
        //     if(resultArray.length === 0 && workerCount === 0) {
        //         Result.innerHTML="Decoding failed.";
        //     }
        // }
    }
    var DecodeWorker = new Worker("/static/js/barcodeReader.js");
    // var RightWorker = new Worker("/static/js/barcodeReader.js");
    // var LeftWorker = new Worker("/static/js/barcodeReader.js");
    var FlipWorker = new Worker("/static/js/barcodeReader.js");

    DecodeWorker.onmessage = receiveMessage;
    // RightWorker.onmessage = receiveMessage;
    // LeftWorker.onmessage = receiveMessage;
    FlipWorker.onmessage = receiveMessage;

    function decodeImage(canvas, ctx){
        var data = ctx.getImageData(0, 0, $(canvas).width(), $(canvas).height()).data;

        // // Theoretically this adds contrast
        // for (var i=0; i < data.length; i++) {
        //     p[i] = p[i]+100 < 255 ? p[i]+100 : 255;
        //     p[i+1] = p[i+1]+100 < 255 ? p[i+1]+100 : 255;
        //     p[i+2] = p[i+2]+100 < 255 ? p[i+2]+100 : 255;
        // }

        DecodeWorker.postMessage({pixels: data, cmd: "normal", skip:["Code39", "Code128", "Code93"]});
        // RightWorker.postMessage({pixels: data, cmd: "right"});
        // LeftWorker.postMessage({pixels: data, cmd: "left"});
        //FlipWorker.postMessage({pixels: data, cmd: "flip"});
    }

    function processCameraImage() {
        var canvas = $("canvas#canvasFeed")[0];
        var video = $("#videoElem")[0];
        var context = canvas.getContext("2d");
        context.drawImage(video, 0, 0, $(video).width(), $(video).height());

        console.log("Got the context");

        decodeImage(canvas, context);
        return false;
    }

    var isCancelled = false;

    $("a#start").click( function(e){
        Camera.startCapture();
        processCameraImage();
        isCancelled = false;
        e.preventDefault();
        flashMessage("success", "barcode capture started");
    });

    $("a#cancel").click( function(e) {
        Camera.pauseCapture();
        isCancelled = true;
        e.preventDefault();
        flashMessage("danger", "barcode capture stopped");
    });

});
