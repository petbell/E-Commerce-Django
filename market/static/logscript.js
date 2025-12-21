const wrapper = document.querySelector('.wrapper');
const loginlink = document.querySelector('.login-link');
const registerlink = document.querySelector('.register-link');
const btnPopup = document.querySelector('.btnlogin-popup');
const iconClose = document.querySelector('.icon-close');

if (registerlink) {
registerlink.addEventListener('click',()=>{
    wrapper.classList.add('active');
});
}

if (loginlink) {
loginlink.addEventListener('click',()=>{
    wrapper.classList.remove('active');
});
}

if (btnPopup) {
btnPopup.addEventListener('click',()=>{
    wrapper.classList.add('active-popup');
});
}

if (iconClose) {
iconClose.addEventListener('click',()=>{
    wrapper.classList.remove ('active-popup');
});
}