import os
from flask import Flask, jsonify, send_from_directory, redirect
from flask_compress import Compress
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from flasgger import Swagger

# Local Imports
import api.utils.responses as resp
from api.config.config import Config, db
from api.config.swagger import swagger_config, swagger_template
from api.utils.logManager import LogManager
from api.utils.responses import response_with, CustomJSONProvider, CustomJSONEncoder
from api.routes.scenario_group import scenarioGroupRoutes
from api.routes.scenario_event import scenarioEventRoutes
from api.routes.scenario import scenarioRoutes
from api.routes.scenario_threshold import scenarioThresholdRoutes
from api.routes.scenario_time_system import scenarioTimeSystemRoutes

# ==========================================
# 初始化應用程式與配置 (Initialization & Config)
# ==========================================
app = Flask(__name__)
app.config.from_object(Config)

# ==========================================
# 擴充套件初始化 (Extensions Initialization)
# ==========================================

# 資料庫與遷移
db.init_app(app)
migrate = Migrate(app, db)

# 壓縮與跨域
Compress(app)
CORS(app)

# JWT
jwt = JWTManager(app)

# Swagger
swagger = Swagger(app, config=swagger_config, template=swagger_template)

# ==========================================
# JSON Provider 設定 (JSON Configuration)
# ==========================================
app.json_encoder = CustomJSONEncoder
app.json_provider_class = CustomJSONProvider
app.json = CustomJSONProvider(app)

# ==========================================
# Log 管理 (Logging)
# ==========================================
logger = LogManager("系統訊息")
log = logger.logger
log.info("系統運行中...")

# ==========================================
# 自定義路由與 Hooks (Custom Routes & Hooks)
# ==========================================
def custom_apispec():
    """
    自定義 Swagger 規範 (apispec) 獲取函數
    
    此函數用於攔截並修改原始的 Swagger 規範 JSON。
    主要功能：
    1. 獲取原始 flasgger 生成的 apispec。
    2. 遍歷所有 API 路徑，將 '/api/' 前綴替換為 '/irs/'。
    3. 返回修改後的規範 JSON。
    
    確保 Swagger UI 在特定路由前綴下能正確顯示和測試 API。
    """
    original_view = app.view_functions['flasgger.apispec']
    response = original_view()
    spec = response.get_json()
    
    # 重寫路徑：將 /api/ 替換為 /irs/
    new_paths = {}
    if 'paths' in spec:
        for path, data in spec['paths'].items():
            new_path = path.replace('/api/', '/irs/', 1)
            new_paths[new_path] = data
        spec['paths'] = new_paths
    return jsonify(spec)

# 註冊 Swagger 自定義路由
app.add_url_rule(
    '/api/docs/apispec.json', 
    endpoint='apispec_internal', 
    view_func=custom_apispec
)

@app.route('/')
def index():
    """根路徑重定向到 API 文檔"""
    return redirect('/api/docs/')

@app.route('/api/static/<path:folder>/<filename>')
def static_file(folder, filename):
    return send_from_directory(f"{app.config['STATIC_FOLDER']}/{folder}", filename)

@app.after_request
def add_header(response):
    return response

# ==========================================
# 錯誤處理 (Error Handlers)
# ==========================================
@app.errorhandler(400)
def bad_request(e):
    log.error(e)
    return response_with(resp.BAD_REQUEST_400)

@app.errorhandler(404)
def not_found(e):
    log.error(e)
    return response_with(resp.SERVER_ERROR_404)

@app.errorhandler(500)
def server_error(e):
    log.error(e)
    return response_with(resp.SERVER_ERROR_500)

# JWT 錯誤處理
@jwt.expired_token_loader
def my_expired_token_callback(jwt_header, jwt_payload):
    log.error(jwt_header, jwt_payload)
    return response_with(resp.UNAUTHORIZED_401, message="token過期")

@jwt.invalid_token_loader
def my_invalid_token_callback(message):
    log.error(message)
    return response_with(resp.UNAUTHORIZED_401, message="無效的token")

@jwt.unauthorized_loader
def my_unauthorized_token_callback(jwt_header):
    log.error(jwt_header)
    return response_with(resp.UNAUTHORIZED_401, message="請求未攜帶token，無許可權訪問")

# ==========================================
# 註冊 Blueprints (Register Blueprints)
# ==========================================
# app.register_blueprint(templateRoutes, url_prefix='/api/template')
app.register_blueprint(scenarioGroupRoutes, url_prefix='/api/irs')
app.register_blueprint(scenarioEventRoutes, url_prefix='/api/irs')
app.register_blueprint(scenarioRoutes, url_prefix='/api/irs')
app.register_blueprint(scenarioThresholdRoutes, url_prefix='/api/irs')
app.register_blueprint(scenarioTimeSystemRoutes, url_prefix='/api/irs')

# ==========================================
# 應用程式啟動前置作業 (Pre-run Setup)
# 使用 Flask-Migrate 時，通常不需要手動 create_all，
# ==========================================
with app.app_context():
    from api.model.scenario_group import ScenarioGroup, ScenarioGroupIntersection
    from api.model.scenario_event import ScenarioEvent
    from api.model.scenario import Scenario
    from api.model.scenario_threshold import ScenarioThreshold
    from api.model.scenario_time_system import ScenarioTimeSystem
    db.create_all()

# ==========================================
# 程式進入點 (Entry Point)
# ==========================================
if __name__ == "__main__":
    app.run(host=os.getenv("HOST"), port=os.getenv("PORT"), debug=True)
