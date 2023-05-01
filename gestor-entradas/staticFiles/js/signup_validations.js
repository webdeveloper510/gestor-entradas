

$(document).ready(function(){
    $('#signupform').validate({
        rules: {
           firstname:"required",
           lastname:"required",
           owners:"required",
           email:"required",
           password: {
            required: true,
            minlength: 5,
           },
           conpassword:{
            required: true,
            minlength: 5,
            equalTo: '[name="password"]'
           },
        },
        messages: {
           firstname: "Please enter Firstname",
           lastname:"Please enter Lastname",
           owners:"Please choose a Role",
           email:"Please enter Email",
           password:{
            required:"please enter Password",
            minlength:"password should be 5 characters"
           },
           conpassword:{
            required:"please enter Confirm Password",
            minlength:"password should be 5 characters",
            equalTo: "Password and confirm password does not match"
           }
        }
    });
});




$(document).ready(function(){
    $('#loginform').validate({
        rules: {
           email:"required",
           password: {
            required: true,
           }
        },
        messages: {
           email:"Please enter Email",
           password:{
            required:"please enter Password",
           }
        }
    });
});

