
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
        image_code_url: '',
        uuid: '',
        image_code: '',
        sms_code: '',
        sms_code_tip: '获取短信验证码',
        send_flag: false,  // false 门开的  true 门关闭的

        // v-show
        error_name: false,
        error_password: false,
        error_password2: false,
        error_mobile: false,
        error_allow: false,
        error_code: false,
        error_sms_code: false,

        // error_message
        error_name_message: "",
        error_code_message: "",
        error_sms_code_message: ""
    },

    // 页面加载完成之后会被调用的方法
    mounted(){
        // 生成图形验证码
        this.generate_image_code();
    },

    methods: {

        // 发送短信验证码 ajax
        send_sms_code(){
            if (this.send_flag == true){
                // 上锁了
                return;
            }
            this.send_flag = true;
            // this.check_mobile();


            // sms_codes/(?P<mobile>1[3-9]\d{9})/
            // register/sms_codes/xxxxx/?uuid=7c508446-cbd9-4450-a22a-e29816c3d
            let url = '/sms_codes/'+ this.mobile +'/?uuid='+ this.uuid +'&image_code=' + this.image_code;
            axios.get(url,{
                responseType: 'json'
            })
                .then(response => {
                    if (response.data.code == '0'){
                        // 展示倒计时60秒
                        let num = 60;
                        // setInterval('回调函数', '时间间隔(毫秒)')
                        let t = setInterval(()=>{
                            if (num == 1){
                                // 停止回调函数
                                clearInterval(t);
                                this.sms_code_tip = '获取短信验证码';

                                // 重新生成图形验证码
                                this.generate_image_code();
                                this.send_flag = false;

                            }else {
                                num -= 1;
                                this.sms_code_tip = num + '秒';
                            }

                        }, 1000)
                    }else {
                        if(response.data.code == '4001'){
                            // 图形验证码错误
                            this.error_sms_code_message = response.data.errmsg;
                            this.error_sms_code = true;
                        }else {
                             // 短信证码错误
                            this.error_sms_code_message = response.data.errmsg;
                            this.error_sms_code = true;
                        }
                        this.send_flag = false;
                    }

                })
                .catch(error => {
                    console.log(error.response);
                    this.send_flag = false;
                })
        },
        // 生成图片验证码
        generate_image_code(){
            // uuid 发生变化
            this.uuid = generateUUID();
            this.image_code_url = '/image_codes/'+ this.uuid +'/'
        },

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


            if (this.error_name == false){

                let url = '/users/usernames/'+ this.username +'/count/';
                // axios.get(url, 请求头(字典))
                axios.get(url, {
                    responseType: 'json'
                })
                    // 请求成功  function(response){}
                    .then(response => {
                        // console.log(this);
                        // console.log(response.data);
                        // alert(response.data.count);
                        if (response.data.count == 1){
                            // 用户名已经存在
                            this.error_name_message = '用户名已经存在';
                            this.error_name = true;
                            // alert(this.error_name);
                        }else {
                            this.error_name = false
                        }
                    })
                    // 请求不成功
                    .catch(error => {
                        console.log(error.response)
                    })
            }

        },

        // 校验密码
        check_password() {
            let re = /^[0-9A-Za-z]{8,20}$/;
            if (re.test(this.password)) {
                this.error_password = false;
            } else {
                this.error_password = true;
            }
        },

        // 校验确认密码
        check_password2() {
            if (this.password != this.password2) {
                this.error_password2 = true;
            } else {
                this.error_password2 = false;
            }
        },

        // 校验手机号
        check_mobile(){
            let re = /^1[3-9]\d{9}$/;
            if (re.test(this.mobile)) {
                this.error_mobile = false;
            } else {
                this.error_mobile_message = '您输入的手机号格式不正确';
                this.error_mobile = true;
            }
        },

        check_allow(){
            if (!this.allow) {
                this.error_allow = true;
            } else {
                this.error_allow = false;
            }
        },

        // 检查图形验证码
        check_image_code(){
            // alert(this.image_code.length);
            if (this.image_code.length != 4){
                this.error_code = true;
                this.error_code_message = '图形验证码长度为4'
            }else {
                this.error_code = false
            }
        },

        // 检查短信验证码
        check_sms_code(){
            if(this.sms_code.length != 6){
                this.error_sms_code_message = '请填写短信验证码';
                this.error_sms_code = true;
            } else {
                this.error_sms_code = false;
            }
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