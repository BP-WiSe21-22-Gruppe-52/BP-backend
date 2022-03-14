import datetime
import hashlib
import json
import locale
import math
import random
import string
import time
from rest_framework.response import Response

from ..Views.leaderboardviews import reset_leaderboard_entry
from ..serializers import CreateExerciseInPlan, CreatePlan

from ..models import Admin, DoneExercises, Exercise, ExerciseInPlan, Location, Trainer, TrainingSchedule, User


SECS_PER_YEAR = 31556952
SECS_PER_DAY = 86400

class ErrorHandler():

    @staticmethod
    def check_arguments(expected_header, header, expected_data, data)->dict:
        missing_header = []
        missing_data = []
        missing = False

        for h in expected_header:
            if header.get(h) == None:
                missing_header.append(h)
                missing = True

        for d in expected_data:
            if data.get(d) == None:
                missing_data.append(d)
                missing = True

        return {
            'valid': not missing,
            'missing': {
                'header': missing_header,
                'data': missing_data
            }
        }

    @staticmethod
    #check length of input
    def check_input_length(input:string, length:int)->bool:
        return len(input)<length

    @staticmethod
    #return data for length
    def length_wrong_response(argument):
        data = {
            'success': False,
            'description': str(argument) + ' is too long',
            'data': {}
        }
        return Response(data)


class PasswordHandler():

    @staticmethod
    def get_random_password(length)->string:
        letters = string.ascii_lowercase
        letters += string.ascii_uppercase
        letters += "0123456789"
        out = ''.join(random.choice(letters) for i in range(length))
        return out

    @staticmethod
    def check_password(username, passwd)->string:
        passwd = str(hashlib.sha3_256(passwd.encode('utf8')).hexdigest())
        if User.objects.filter(username=username, password=passwd).exists():
            return "user"
        elif Trainer.objects.filter(username=username, password=passwd).exists():
            return "trainer"
        elif Admin.objects.filter(username=username, password=passwd).exists():
            return "admin"
        else:
            return "invalid"


class UserHandler():

    @staticmethod
    def set_user_language(username, language, max_length)->bool:
        if max_length < len(language):
            return False
        if User.objects.filter(username=username).exists():
            user:User = User.objects.get(username=username)
        elif Trainer.objects.filter(username=username).exists():
            user:Trainer = Trainer.objects.get(username=username)
        elif Admin.objects.filter(username=username).exists():
            user:Admin = Admin.objects.get(username=username)
        else:
            return False
        user.language = language
        user.save(force_update=True)
        return True

    @staticmethod
    def get_user_language(username)->string:
        if User.objects.filter(username=username).exists():
            user:User = User.objects.get(username=username)
        elif Trainer.objects.filter(username=username).exists():
            user:Trainer = Trainer.objects.get(username=username)
        elif Admin.objects.filter(username=username).exists():
            user:Admin = Admin.objects.get(username=username)
        else:
            return None
        return user.language

    @staticmethod
    def add_xp(user:User, xp)->bool:
        user.xp += xp
        user.save(force_update=True)
        return True

    @staticmethod
    def calc_level(xp:int, max:int)->tuple:
        for i in range(max):
            nxt_lvl = math.ceil(300 * 1.25 ** (i))
            if xp < nxt_lvl:
                return i, str(xp)+'/'+str(nxt_lvl)
            xp -= nxt_lvl
        return max, 'max level reached'

    @staticmethod
    #only method needs to be changed to get different information about users
    def get_users_data_for_upper(users)->list:
        data = []
        for user in users:
            #getting plan id
            if user.plan == None:
                plan_id = None
                perc_done = None
            else:
                plan_id = user.plan.id
                #getting weekly progress
                done = ExerciseHandler.get_done(user)
                if done.get('success'):
                    exs = done.get('data').get('exercises')
                    nr_of_done = 0
                    for ex in exs:
                        if ex.get('done'):
                            nr_of_done += 1
                    all = len(exs)
                    perc_done = math.ceil((nr_of_done/all)*10000)/10000
                else:
                    perc_done = None
            data.append({
                'id': user.id,
                'username': user.username,
                'plan': plan_id,
                'done_exercises': perc_done,
                'last_login': user.last_login
            })
        return data

    @staticmethod
    #set last login
    def last_login(username)->None:
        locale.setlocale(locale.LC_ALL, 'en_US.utf8')
        now = datetime.datetime.now()
        year = now.year
        month = now.month
        day = now.day
        today = DateHandler.get_string_of_date(day, month, year)
        weekday = now.strftime('%A').lower()
        if not User.objects.filter(username=username).exists():
            #if its trainer only set last login
            if not Trainer.objects.filter(username=username).exists():
                return
            else:
                username:Trainer = Trainer.objects.get(username=username)
        else:
            username:User = User.objects.get(username=username)
            UserHandler.check_keep_streak(username)
            if username.last_login != today:
                if username.plan is None:
                    username.all_done = True
                elif ExerciseInPlan.objects.filter(plan=username.plan, date=weekday):
                    username.all_done = False
                else:
                    username.all_done = True
        username.last_login = today
        username.save(force_update=True)

    @staticmethod
    #check streak, not updated if today everything is done
    def check_keep_streak(user:User)->None:
        locale.setlocale(locale.LC_ALL, 'en_US.utf8')
        today = datetime.datetime.today()
        #if user never logged in, streak=0
        if user.last_login is None:
            user.streak = 0
            user.save(force_update=True)
            return
        #if user already logged in today return
        if user.last_login == DateHandler.get_string_of_date(today.day, today.month, today.year):
            return
        count = 0
        #until the last login check for every day if every exercise has been done
        while True:
            count += 1
            day_before = today - datetime.timedelta(days=count)
            weekday = day_before.strftime('%A').lower()
            exips = ExerciseInPlan.objects.filter(plan=user.plan, date=weekday)
            #if there had not to be done any exercises, check if that's last login
            if exips.exists():
                for exip in exips:
                    #calculate period in which exercise had to be done
                    if not DoneExercises.objects.filter(exercise=exip, user=user, date__gt=time.time() - (count * 86400) - time.time() % 86400, date__lt=time.time() - ((count-1) * 86400) - time.time() % 86400 ).exists():
                        #if in this period no exercise has been done
                        user.streak = 0
                        user.save(force_update=True)
                        return
                    #if all exercises had been done return, because after every exercise increasing streak is checked
                    return
            #check if that's last login, else check next day
            if user.last_login == DateHandler.get_string_of_date(day_before.day, day_before.month, day_before.year):
                return

    @staticmethod
    #just this method has to be changed to get more information for profile
    def get_profile_data(user:User)->dict:
        return {
            'username': user.username,
            'avatar': user.avatar,
            'first_login': user.first_login,
            'motivation': user.motivation
        }    

    @staticmethod
    #only method needs to be changed to get different information about users
    def get_users_data(users)->list:
        data = []
        for user in users:
            data.append({
                'id': user.id,
                'username': user.username
            })
        return data

    @staticmethod
    def check_flame_glow(user:User)->bool:
        today = datetime.datetime.now()
        weekday = today.strftime('%A').lower()
        exips = ExerciseInPlan.objects.filter(plan=user.plan, date=weekday)
        #if there had not to be done any exercises, check if that's last login
        if exips.exists():
            for exip in exips:
                #calculate period in which exercise had to be done
                if not DoneExercises.objects.filter(exercise=exip, user=user, date__gt=time.time() - time.time() % 86400).exists():
                    #if in this period no exercise has been done
                    return False
            #if all exercises had been done return, because after every exercise increasing streak is checked
            return True
        #no exercise
        return True


class TrainerHandler():

    @staticmethod
    #only method needs to be changed to get different information about users
    def get_trainers_data(trainers)->list:
        data = []
        for trainer in trainers:
            data.append({
                'id': trainer.id,
                'username': trainer.username,
                'last_login': trainer.last_login
            })
        return data

    @staticmethod
    #just this method has to be changed to get more contact information for trainers
    def get_trainer_contact(trainer:Trainer, as_user:bool)->dict:
        loc:Location = trainer.location
        # check if trainer has location
        if loc is None:
            location = None
        else:
            # concatenate location
            location = loc.street + ' ' + loc.house_nr + loc.address_addition + ', ' + loc.postal_code + ' ' + loc.city + ', ' + loc.country
        academia = trainer.academia
        if academia is None or len(academia) == 0:
            academia = ''
        else:
            academia += ' '
        name = str(academia + trainer.first_name + ' ' + trainer.last_name)
        if as_user:
            return {
                'name': name,
                'address': str(location),
                'telephone': trainer.telephone,
                'email': trainer.email_address
            }
        else:
            return {
                'name': name,
                'academia': trainer.academia,
                'street': loc.street if loc is not None else "",
                'city': loc.city if loc is not None else "",
                'country': loc.country if loc is not None else "",
                'address_addition': loc.address_addition if loc is not None else "",
                'postal_code': loc.postal_code if loc is not None else "",
                'house_nr': loc.house_nr if loc is not None else "",
                'telephone': trainer.telephone,
                'email': trainer.email_address
            }


class PlanHandler():

    @staticmethod
    def add_plan_to_user(username, plan)->string:
        #checks if user exists
        if not User.objects.filter(username=username).exists():
            return "user_invalid"
        #checks if plan exists
        if plan != None:
            if not TrainingSchedule.objects.filter(id=int(plan), visable = True).exists():
                    return "plan_invalid"
        #assign plan to user
        user:User = User.objects.get(username=username)
        if plan == None:
            ts = None
        else:
            ts:TrainingSchedule = TrainingSchedule.objects.get(id=int(plan))
        user.plan = ts
        user.save(force_update=True)

        reset_leaderboard_entry(username)
        return "success"

    @staticmethod
    def create_plan(trainer:Trainer, name:string)->tuple:
        #create plan
        data = {
            'trainer': trainer,
            'name': name
        }
        new_plan = CreatePlan(data=data)
        #check if plan is valid
        if new_plan.is_valid():
            plan = new_plan.save()
            return "valid", plan
        else:
            return "invalid", new_plan.errors

    @staticmethod
    def add_exercise_to_plan(plan:TrainingSchedule, date:string, sets:int, rps:int, exercise:Exercise)->tuple:
        #create plan data
        data = {
            'date': date,
            'sets': sets,
            'repeats_per_set': rps,
            'exercise': exercise,
            'plan': plan.id
        }
        new_data = CreateExerciseInPlan(data=data)
        #check if plan data is valid
        if new_data.is_valid():
            data = new_data.save()
            return "success", data
        return "invalid", new_data.errors

    @staticmethod
    def getListOfExercises(plan:TrainingSchedule)->list:
        exs = []
        plan_data = ExerciseInPlan.objects.filter(plan=plan)
        for ex in plan_data:
            ex_id = ex.exercise.id
            sets = ex.sets
            rps = ex.repeats_per_set
            date = ex.date
            exs.append({
                'exercise_plan_id': ex.id,
                'id': ex_id,
                'sets': sets,
                'repeats_per_set': rps,
                'date': date
            })
        return exs


class LanguageHandler():

    @staticmethod
    def get_in_correct_language(username:string, description:string)->string:
        if User.objects.filter(username=username).exists():
            user:User = User.objects.get(username=username)
        elif Trainer.objects.filter(username=username).exists():
            user:Trainer = Trainer.objects.get(username=username)
        elif Admin.objects.filter(username=username).exists():
            user:Admin = Admin.objects.get(username=username)
        else:
            return "invalid user"
        lang = user.language
        desc:dict = json.loads(description.replace("'", "\""))
        res = desc.get(lang)
        if res == None:
            return lang + " is not available"
        return res


class ExerciseHandler():

    @staticmethod
    def get_done_exercises_of_month(month:int, year:int, user:User)->list:
        year_offset = (year-1970)*SECS_PER_YEAR
        month_offset = 0
        for i in range(1, month):
            month_offset += DateHandler.get_lastday_of_month(i, year)*SECS_PER_DAY
        next_month_offset = month_offset + DateHandler.get_lastday_of_month(month, year) * SECS_PER_DAY
        offset_gt = year_offset + month_offset
        offset_lt = year_offset + next_month_offset
        done = DoneExercises.objects.filter(user=user, date__gt=offset_gt, date__lt=offset_lt, completed=True)
        # list of all exercises to done
        all = ExerciseInPlan.objects.filter(plan=user.plan)
        out = []
        for d in done:
            out.append({
                "exercise_plan_id": d.exercise.id,
                "id": d.exercise.exercise.id,
                "date": d.date,
                "points": d.points
            })
        return out

    @staticmethod
    def get_done(user:User):

        # list of all done in last week
        # calculation of timespan and filter
        done = DoneExercises.objects.filter(user=user, date__gt=time.time() + 86400 - time.time() % 86400 - 604800, completed=True)
        # list of all exercises to done
        all = ExerciseInPlan.objects.filter(plan=user.plan)
        out = []
        for a in all:
            done_found = False
            for d in done:
                if done_found:
                    continue
                if a.id == d.exercise.id:
                    out.append({"exercise_plan_id": a.id,
                                "id": a.exercise.id,
                                "date": a.date,
                                "sets": a.sets,
                                "repeats_per_set": a.repeats_per_set,
                                "done": True
                                })
                    done_found = True
                    break
            if done_found:
                continue

            out.append({"exercise_plan_id": a.id,
                        "id": a.exercise.id,
                        "date": a.date,
                        "sets": a.sets,
                        "repeats_per_set": a.repeats_per_set,
                        "done": False
                        })



        data = {
            "success": True,
            "description": "Returned list of Exercises and if its done",
            "data":
                {"name": user.plan.name,
                 "exercises": out
                 }
        }

        #returns the data as in the get plan but with a additional var "done"
        return data


class InvitationsHandler():

    @staticmethod
    def get_invited_data(open_tokens)->list:
        data = []
        for ot in open_tokens:
            data.append({
                'id': ot.id,
                'first_name': ot.first_name,
                'last_name': ot.last_name,
                'email': ot.email
            })
        return data


class DateHandler():

    @staticmethod
    def get_lastday_of_month(m:int, y:int)->int:
        if m == 1 or m == 3 or m == 5 or m == 7 or m == 8 or m == 10 or m == 12:
            return 31
        elif m == 4 or m == 6 or m == 9 or m == 11:
            return 30
        elif m == 2:
            if y % 400 == 0:
                return 29
            elif y % 100 == 0:
                return 28
            elif y % 4 == 0:
                return 29
            else:
                return 28
        else:
            return -1

    @staticmethod
    def get_string_of_date(d:int, m:int, y:int)->string:
        if d < 10:
            day = '0'+str(d)
        else:
            day = str(d)
        if m < 10:
            month = '0'+str(m)
        else:
            month = str(m)
        return str(y)+'-'+str(month)+'-'+str(day)

    @staticmethod
    def valid_month(month:int)->bool:
        if (month < 1) or (month > 12):
            return False
        return True