# сценарий логина
from scenarios.login_scenario import login
from scenarios.login_scenario import logout
from scenarios.login_scenario import connect_to_admin
# сценарий обучения модели
from scenarios.model_teach_scenario import model_creation_page
from scenarios.model_teach_scenario import continue_with_model
from scenarios.model_teach_scenario import upload_dataset
from scenarios.model_teach_scenario import save_upload_data
from scenarios.model_teach_scenario import set_data_table_for_model
from scenarios.model_teach_scenario import set_params_for_model
from scenarios.model_teach_scenario import teach_model
# сценарий копирования незавершённой модели
from scenarios.model_copy_scenario import copy_unfinished_model
# сценарий просмотра характеристик незавершённых моделей
from scenarios.model_description_scenario import incomplete_model
from scenarios.model_description_scenario import delete_model
# сценарий тестирования обученных моделей на новых данных
from scenarios.model_test_scenario import test_new_model
# сценарий назначения финализированной модели
from scenarios.model_use_scenario import model_for_use
# сценарий сравнения финализированных моделей
from scenarios.model_fin_compare_scenario import compare_fin_models
# сценарий просмотра очереди на обучение
from scenarios.model_queue_scenario import check_queue
# сценарий архивации/разархивации данных/моделей в холодное хранилище
from scenarios.model_archive_scenario import archive_work
