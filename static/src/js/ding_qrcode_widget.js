/** @odoo-module */

import {registry} from "@web/core/registry";

const {Component, xml, useEffect, onWillStart} = owl;
import {loadJS} from "@web/core/assets";
import {useService} from "@web/core/utils/hooks";

class DingTalkQrcode extends Component {
    setup() {
        this.rpc = useService("rpc");

        onWillStart(() => loadJS("https://g.alicdn.com/dingding/h5-dingtalk-login/0.21.0/ddlogin.js"));

        useEffect(async () => {
            // to safety, we can not request by search_read, so we use rpc
            const app = await this.rpc('/ding/oauth2/info', {
                app_id: this.props.appId
            })

            window.DTFrameLogin(
                {
                    id: 'ding_reg',
                    width: 300,
                    height: 300,
                },
                {
                    redirect_uri: encodeURIComponent(app.redirect_uri),
                    client_id: app.client_id,
                    scope: 'openid',
                    response_type: 'code',
                    prompt: 'consent'
                },
                (loginResult) => {
                    const {redirectUrl, authCode} = loginResult;
                    // 这里可以直接进行重定向
                    window.location.href = redirectUrl;
                },
                (errorMsg) => {
                    // 这里一般需要展示登录失败的具体原因
                    alert(`Login Error: ${errorMsg}`);
                },
            );
        }, () => [])
    }
}

DingTalkQrcode.template = xml`
<div style="width: 100%;height: 100%">
    <div id="ding_reg" style="width: 100%;height: 100%;display: flex;justify-content: center;align-items: center;"></div>
</div>
`;

DingTalkQrcode.defaultProps = {
    appId: "",
};
DingTalkQrcode.extractProps = ({attrs}) => {
    return {
        appId: attrs.app_id,
    };
};

registry.category("view_widgets").add("ding_qrcode", DingTalkQrcode);