
let vm = new Vue({
    el: '#app',  // 通过ID选择器找到绑定的HTML内容
    delimiters: ['[[', ']]'],    // 修改Vue读取变量的语法
    data: {     // 数据对象
        // v-model
        username: '',
        password: '',
        password2: '',
        mobile: '',
        allow: '',

        // v-show
        error_name: false,
        error_password: false,
        error_password2: false,
        error_mobile: false,
        error_allow: false,

        // error_message
        error_name_message: ""
    },
    methods: {
        // 检验用户名
        check_username(){

            // 5-20 [a-zA-Z0-9_-]
            let re = /^[a-zA-Z0-9_-]{5,20}$/;
            if (re.test(this.username)){
                // 匹配 不展示错误提示信息
                this.error_name = false;
            }else {
                this.error_name = true;
                this.error_name_message = '请输入5-20个字符的用户名';
            }
        },
        // 检查密码
        check_password(){

        },
        check_password2(){

        },
        check_mobile(){

        },
        check_allow(){

        },
        on_submit(){
            this.check_username();
            this.check_password();
            this.check_password2();
            this.check_mobile();
            this.check_allow();

            if (this.error_name == true || this.error_password == true || this.error_password2 == true ||  this.error_mobile == true || this.error_allow == true){
                // 禁用掉表单的提交事件
                window.event.returnValue = false;
            }

        }
    }
});