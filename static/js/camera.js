(function() {

    console.log('Loading camera.js');

    var videoElem = document.getElementById("videoElem");
    var canvasElem = document.getElementById("canvasFeed");

    console.log('Have access to canvases', videoElem, canvasElem);

    var whenUserGrantsAccess = function (mediaStreamObject) {
        console.log('User granted access to camera');
        console.log(mediaStreamObject);

        videoElem.src = window.URL.createObjectURL(mediaStreamObject);

        // Tell the video element to 'play' the stream from the camera
        videoElem.play();

        // Get our canvas's 2d context
        var context = canvasElem.getContext('2d');

        // Set our draw context to 'mirror'
        // context.translate(canvasElem.width, 0);
        // context.scale(-1, 1);

        // Start to draw the video into the canvas

        // var drawSingleFrame = function () {

        //     context.drawImage(videoElem, 0, 0, videoElem.width, videoElem.height);

        // };

        // //
        // setInterval(drawSingleFrame, 500);
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

    console.log('I\'m doing other shit');

})();
