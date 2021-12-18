from django.test import TestCase
from django.test.utils import setup_test_environment
from .models import *
from .Views.userviews import *
from .Helperclasses.jwttoken import *
from .Helperclasses.fortests import *

class UserTestCase(TestCase):

    trainer_id = 1

    def setUp(self):
        Trainer.objects.create(first_name="Erik", last_name="Prescher", username="DerTrainer", email_address="prescher-erik@web.de", password="Password1234")
        trainer = Trainer.objects.get(first_name="Erik")
        self.trainer_id = trainer.id
        User.objects.create(first_name="Erik", last_name="Prescher", username="DeadlyFarts", trainer=trainer, email_address="prescher-erik@web.de", password="Password1234")

    def test_if_exists(self):
        self.assertTrue(Trainer.objects.filter(first_name="Erik", last_name="Prescher", username="DerTrainer", email_address="prescher-erik@web.de", password="Password1234").exists())
        self.assertTrue(User.objects.filter(first_name="Erik", last_name="Prescher", username="DeadlyFarts", trainer=self.trainer_id, email_address="prescher-erik@web.de", password="Password1234").exists())

    def test_if_user_gets_deleted_when_trainer_gets_deleted(self):
        Trainer.objects.filter(first_name="Erik", last_name="Prescher", username="DerTrainer", email_address="prescher-erik@web.de", password="Password1234").delete()
        self.assertFalse(Trainer.objects.filter(first_name="Erik", last_name="Prescher", username="DerTrainer", email_address="prescher-erik@web.de", password="Password1234").exists())
        self.assertFalse(User.objects.filter(first_name="Erik", last_name="Prescher", username="DeadlyFarts", trainer=self.trainer_id, email_address="prescher-erik@web.de", password="Password1234").exists())


class DeleteUserTestCase(TestCase):

    user_id = 1
    user_id_2 = 2
    trainer_id = 1
    exercise_id = 1
    done_ex_id = 1
    friends_id = 1

    def setUp(self):
        Trainer.objects.create(first_name="Erik", last_name="Prescher", username="DerTrainer", email_address="prescher-erik@web.de", password="Password1234")
        trainer = Trainer.objects.get(first_name="Erik")
        DeleteUserTestCase.trainer_id = trainer.id
        User.objects.create(first_name="Erik", last_name="Prescher", username="DeadlyFarts", trainer=trainer, email_address="prescher-erik@web.de", password="Password1234")
        User.objects.create(first_name="Jannis", last_name="Bauer", username="jbad", trainer=trainer, email_address="test@bla.de", password="Password1234")
        user1 = User.objects.get(first_name='Erik')
        user2 = User.objects.get(first_name='Jannis')
        DeleteUserTestCase.user_id = user1.id
        DeleteUserTestCase.user_id_2 = user2.id
        Exercise.objects.create(title='Squat', description='Just do it.')
        exercise = Exercise.objects.get(title='Squat')
        DeleteUserTestCase.exercise_id = exercise.id
        DoneExercises.objects.create(exercise=exercise, user=user1, points=98)
        DeleteUserTestCase.done_ex_id = DoneExercises.objects.get(points=98).id
        Friends.objects.create(friend1=user1, friend2=user2)
        DeleteUserTestCase.friends_id = Friends.objects.get(friend1=DeleteUserTestCase.user_id).id

    def test_cascade(self):
        User.objects.filter(id=DeleteUserTestCase.user_id).delete()
        self.assertTrue(User.objects.filter(id=DeleteUserTestCase.user_id_2).exists())
        self.assertTrue(Trainer.objects.filter(id=DeleteUserTestCase.trainer_id).exists())
        self.assertTrue(Exercise.objects.filter(id=DeleteUserTestCase.exercise_id).exists())
        self.assertFalse(User.objects.filter(id=DeleteUserTestCase.user_id).exists())
        self.assertFalse(DoneExercises.objects.filter(id=DeleteUserTestCase.done_ex_id).exists())
        self.assertFalse(Friends.objects.filter(id=DeleteUserTestCase.friends_id).exists())


class ExerciseTestCase(TestCase):
    def setUp(self):
        Exercise.objects.create(title='Kniebeuge', description="Gehe in die Knie, achte...")
        Exercise.objects.create(title='Liegestütze', description="Mache Liegestütze", activated=False)

    def test_if_exists(self):
        self.assertTrue(Exercise.objects.filter(title='Kniebeuge', description="Gehe in die Knie, achte...", video=None, activated=True).exists())
        self.assertTrue(Exercise.objects.filter(title='Liegestütze', description="Mache Liegestütze", video=None, activated=False).exists())

    def test_if_delete_works(self):
        Exercise.objects.filter(title='Kniebeuge', description="Gehe in die Knie, achte...", video=None, activated=True).delete()
        Exercise.objects.filter(title='Liegestütze', description="Mache Liegestütze", video=None, activated=False).delete()
        self.assertFalse(Exercise.objects.filter(title='Kniebeuge', description="Gehe in die Knie, achte...", video=None, activated=True).exists())
        self.assertFalse(Exercise.objects.filter(title='Liegestütze', description="Mache Liegestütze", video=None, activated=False).exists())


class PlanTestCase(TestCase):

    trainer_id = 0
    user_id = 0
    ex_id = 0
    ts_id = 0

    def setUp(self):
        Trainer.objects.create(first_name="Erik", last_name="Prescher", username="DerTrainer", email_address="prescher-erik@web.de", password="Password1234")
        trainer = Trainer.objects.get(first_name="Erik")
        self.trainer_id = trainer.id
        User.objects.create(first_name="Erik", last_name="Prescher", username="DeadlyFarts", trainer=trainer, email_address="prescher-erik@web.de", password="Password1234")
        user = User.objects.get(first_name="Erik")
        self.user_id = user.id
        Exercise.objects.create(title='Kniebeuge', description="Gehe in die Knie, achte...")
        ex = Exercise.objects.get(title='Kniebeuge')
        self.ex_id = ex.id
        TrainingSchedule.objects.create(trainer=trainer)
        ts = TrainingSchedule.objects.get(trainer=trainer.id)
        self.ts_id = ts.id
        ExerciseInPlan.objects.create(date="monday", sets=5, repeats_per_set=10, exercise=ex, plan=ts)
        user.plan = ts
        user.save()

    def test_if_exists(self):
        self.assertTrue(TrainingSchedule.objects.filter(trainer=self.trainer_id).exists())
        self.assertTrue(ExerciseInPlan.objects.filter(exercise=self.ex_id, plan=self.ts_id).exists())
        self.assertTrue(User.objects.filter(first_name="Erik").exists())
        user = User.objects.get(first_name="Erik")
        self.assertEquals(user.plan.id, self.ts_id)

    def test_if_related_deletes_work(self):
        #test cascade if Exercise is deleted
        Exercise.objects.filter(title='Kniebeuge').delete()
        self.assertFalse(ExerciseInPlan.objects.filter(exercise=self.ex_id, plan=self.ts_id))
        #recreate data
        Exercise.objects.create(title='Kniebeuge', description="Gehe in die Knie, achte...")
        ex = Exercise.objects.get(title='Kniebeuge')
        self.ex_id = ex.id
        ts = TrainingSchedule.objects.get(id=self.ts_id)
        ExerciseInPlan.objects.create(date="monday", sets=5, repeats_per_set=10, exercise=ex, plan=ts)
        #test cascade if Trainer is deleted
        Trainer.objects.filter(first_name="Erik").delete()
        self.assertFalse(User.objects.filter(first_name="Erik").exists())
        self.assertFalse(TrainingSchedule.objects.filter(id=self.ts_id).exists())
        self.assertFalse(ExerciseInPlan.objects.filter(exercise=self.ex_id, plan=self.ts_id))
        #recreate data        
        Trainer.objects.create(first_name="Erik", last_name="Prescher", username="DerTrainer", email_address="prescher-erik@web.de", password="Password1234")
        trainer = Trainer.objects.get(first_name="Erik")
        self.trainer_id = trainer.id
        User.objects.create(first_name="Erik", last_name="Prescher", username="DeadlyFarts", trainer=trainer, email_address="prescher-erik@web.de", password="Password1234")
        user = User.objects.get(first_name="Erik")
        self.user_id = user.id
        TrainingSchedule.objects.create(trainer=trainer)
        ts = TrainingSchedule.objects.get(trainer=self.trainer_id)
        self.ts_id = ts.id
        ExerciseInPlan.objects.create(date="monday", sets=5, repeats_per_set=10, exercise=ex, plan=ts)
        user.plan = ts
        user.save()
        #delete plan
        TrainingSchedule.objects.filter(id=self.ts_id).delete()
        self.assertFalse(TrainingSchedule.objects.filter(id=self.ts_id).exists())
        user = User.objects.get(first_name="Erik")
        self.assertFalse(ExerciseInPlan.objects.filter(exercise=self.ex_id, plan=self.ts_id))
        self.assertEquals(user.plan, None)


class TestUserViews(TestCase):

    trainer_id = 1
    user_id = 1
    trainer_token = None
    user_token = None
    user_refresh_token = None
    admin_token = None

    def setUp(self):
        Trainer.objects.create(first_name="Erik", last_name="Prescher", username="DerTrainer", email_address="prescher-erik@web.de", password="Password1234")
        trainer = Trainer.objects.get(first_name="Erik")
        self.trainer_id = trainer.id
        User.objects.create(first_name="Erik", last_name="Prescher", username="DeadlyFarts", trainer=trainer, email_address="prescher-erik@web.de", password=str(hashlib.sha3_256("Password1234".encode('utf8')).hexdigest()))
        Admin.objects.create(first_name="Erik", last_name="Prescher", username="derAdmin", password="Password1234")
        user = User.objects.get(first_name="Erik")
        self.user_id = user.id
        admin = Admin.objects.get(first_name="Erik")
        self.trainer_token = JwToken.create_session_token(trainer.username, 'trainer')
        self.user_token = JwToken.create_session_token(user.username, 'user')
        self.admin_token = JwToken.create_session_token(admin.username, 'admin')

    def test_delete_account(self):
        request = ViewSupport.setup_request({'Session-Token': self.user_token}, {})
        response = DeleteAccountView.post(self=APIView, request=request) 
        self.assertTrue(response.data.get('success'))
        self.assertFalse(User.objects.filter(id=self.user_id).exists())
        #setup user again
        trainer = Trainer.objects.get(id=self.trainer_id)
        User.objects.create(first_name="Erik", last_name="Prescher", username="DeadlyFarts", trainer=trainer, email_address="prescher-erik@web.de", password=str(hashlib.sha3_256("Password1234".encode('utf8')).hexdigest()))
        user = User.objects.get(first_name="Erik")
        self.user_id = user.id

    def test_login(self):
        #correct
        request = ViewSupport.setup_request({}, {
                'username': "DeadlyFarts",
                'password': "Password1234" 
            })
        response = LoginView.post(LoginView, request)
        self.assertTrue(response.data.get('success'))
        self.user_token = response.data.get('data').get('session_token')
        self.user_refresh_token = response.data.get('data').get('refresh_token')
        self.assertTrue(JwToken.check_session_token(self.user_token))
        self.assertTrue(JwToken.check_refresh_token(self.user_refresh_token))
        #invalid username
        request = ViewSupport.setup_request({}, {
                'username': "cooleKids",
                'password': "Password1234" 
            })
        response = LoginView.post(LoginView, request)
        self.assertFalse(response.data.get('success'))
        #invalid username
        request = ViewSupport.setup_request({}, {
                'username': "DeadlyFarts",
                'password': "wrong" 
            })
        response = LoginView.post(LoginView, request)
        self.assertFalse(response.data.get('success'))
    
    def test_register(self):
        #TODO
        self.assertTrue(True)

    def test_createUser(self):
        #TODO
        self.assertTrue(True)

    def test_auth(self):
        #correct
        request = ViewSupport.setup_request({}, {
                'refresh': self.user_refresh_token
            })
        if self.user_refresh_token != None:
            response = AuthView.post(AuthView, request)
            self.assertTrue(response.data.get('success'))
        #TODO else create refresh-token

    def test_logoutAllDevices(self):
        #TODO
        self.assertTrue(True)


class TestExerciseView(TestCase):

    trainer_id = 1
    trainer_token = None
    user_token = None
    admin_token = None

    def setUp(self):
        Exercise.objects.create(title='Kniebeuge', description="Gehe in die Knie, achte...")
        Exercise.objects.create(title='Liegestütze', description="Mache Liegestütze", activated=False)

        Trainer.objects.create(first_name="Erik", last_name="Prescher", username="DerTrainer", email_address="prescher-erik@web.de", password="Password1234")
        trainer = Trainer.objects.get(first_name="Erik")
        self.trainer_id = trainer.id
        User.objects.create(first_name="Erik", last_name="Prescher", username="DeadlyFarts", trainer=trainer, email_address="prescher-erik@web.de", password="Password1234")
        Admin.objects.create(first_name="Erik", last_name="Prescher", username="derAdmin", password="Password1234")
        user = User.objects.get(first_name="Erik")
        admin = Admin.objects.get(first_name="Erik")
        self.trainer_token = JwToken.create_session_token(trainer.username, 'trainer')
        self.user_token = JwToken.create_session_token(user.username, 'user')
        self.admin_token = JwToken.create_session_token(admin.username, 'admin')

    def test_get(self):
        #TODO
        self.assertTrue(True)

    def test_get_list(self):
        #TODO
        self.assertTrue(True)


class TestPlanView(TestCase):

    trainer_token = None
    user_token = None

    def setUp(self):
        Trainer.objects.create(first_name="Erik", last_name="Prescher", username="DerTrainer", email_address="prescher-erik@web.de", password="Password1234")
        trainer = Trainer.objects.get(first_name="Erik")
        User.objects.create(first_name="Erik", last_name="Prescher", username="DeadlyFarts", trainer=trainer, email_address="prescher-erik@web.de", password="Password1234")
        user = User.objects.get(first_name="Erik")
        self.trainer_token = JwToken.create_session_token(trainer.username, 'trainer')
        self.user_token = JwToken.create_session_token(user.username, 'user')

    def test_create_new(self):
        #TODO
        self.assertTrue(True)

    def test_create_change(self):
        #TODO
        self.assertTrue(True)

    def test_add_user(self):
        #TODO
        self.assertTrue(True)

    def test_get_list(self):
        #TODO
        self.assertTrue(True)

    def test_get(self):
        #TODO
        self.assertTrue(True)

    def test_get_for_user(self):
        #TODO
        self.assertTrue(True)

    def test_delete(self):
        #TODO
        self.assertTrue(True)
