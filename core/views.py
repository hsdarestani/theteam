import calendar
from datetime import timedelta
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .forms import EventForm, EvaluationForm, MatchForm, MatchPerformanceForm, PlayerForm, ReportNoteForm, SetupForm, TaskForm, TrainingForm
from .models import Attendance, Match, MatchPerformance, Player, PlayerEvaluation, ReportNote, TaskAssignment, TeamEvent, TrainingSession


def health(request):
    return JsonResponse({"status":"ok"})

def setup(request):
    if get_user_model().objects.exists():
        return redirect("login")
    form = SetupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save(); login(request, user)
        seed_demo_data(user)
        messages.success(request, "Das Teamboard ist startklar.")
        return redirect("dashboard")
    return render(request, "core/setup.html", {"form":form})

def seed_demo_data(user):
    if Player.objects.exists(): return
    names = [
        (1,"Lukas","Adler","Torwart","Deutschland"),(3,"Milan","Voss","Innenverteidigung","Deutschland"),(4,"Jonas","Keller","Innenverteidigung","Deutschland"),
        (8,"Elias","Hartmann","Mittelfeld","Österreich"),(15,"Noah","Berger","Mittelfeld","Deutschland"),(16,"Leon","Falk","Mittelfeld","Schweiz"),
        (19,"Mika","Sommer","Flügel","Deutschland"),(27,"David","Kramer","Mittelfeld","Deutschland"),(7,"Samir","Aydin","Sturm","Deutschland"),
        (11,"Finn","Wagner","Sturm","Deutschland"),(13,"Emil","Brandt","Rechtsverteidigung","Dänemark"),(35,"Mateo","Silva","Innenverteidigung","Portugal")]
    players=[]
    for number, first,last,pos,nat in names:
        players.append(Player.objects.create(shirt_number=number,first_name=first,last_name=last,position=pos,nationality=nat))
    now=timezone.now()
    TeamEvent.objects.bulk_create([
        TeamEvent(title="Teamtraining",event_type="training",starts_at=now+timedelta(days=1,hours=2),location="Trainingszentrum",created_by=user),
        TeamEvent(title="Spielvorbereitung",event_type="meeting",starts_at=now+timedelta(days=2,hours=4),location="Besprechungsraum 2",created_by=user),
        TeamEvent(title="vs. FC Rheinstadt",event_type="match",starts_at=now+timedelta(days=4,hours=6),location="Deutsche Bank Park",created_by=user),
    ])
    training=TrainingSession.objects.create(title="Teamtraining",starts_at=now+timedelta(days=1,hours=2),ends_at=now+timedelta(days=1,hours=4),location="Trainingszentrum",focus="Pressing, Umschalten, Standards",created_by=user)
    for p in players:
        Attendance.objects.create(training=training,player=p,status="present")
    Attendance.objects.filter(training=training,player=players[-1]).update(status="injured",comment="Individuelles Programm")
    TaskAssignment.objects.create(training=training,player=players[0],task="Materialcheck mit Athletikteam")
    match=Match.objects.create(opponent="FC Rheinstadt",kickoff=now-timedelta(days=3),competition="Bundesliga",location="Deutsche Bank Park",venue="home",goals_for=2,goals_against=1,created_by=user)
    for i,p in enumerate(players[:8]):
        base=7+(i%3)
        MatchPerformance.objects.create(match=match,player=p,minutes_played=90 if i<6 else 30,mentality=min(base,10),physicality=max(base-1,1),performance=min(base+(1 if i==6 else 0),10),comment="Konzentrierter Auftritt." if i%2==0 else "Gute Intensität und klare Aktionen.")
        PlayerEvaluation.objects.create(player=p,mentality=min(base,10),physicality=max(base-1,1),performance=base,potential=min(base+1,10),coach=user,comment="Stabile Entwicklung im aktuellen Trainingsblock.")

@login_required
def dashboard(request):
    now=timezone.now()
    players=Player.objects.filter(active=True)
    upcoming=TeamEvent.objects.filter(starts_at__gte=now)[:4]
    next_training=TrainingSession.objects.filter(starts_at__gte=now,status="planned").first()
    availability=players.values("status").annotate(total=Count("id"))
    status_counts={x["status"]:x["total"] for x in availability}
    avg=PlayerEvaluation.objects.aggregate(mentality=Avg("mentality"),physicality=Avg("physicality"),performance=Avg("performance"))
    recent_eval=PlayerEvaluation.objects.select_related("player").first()
    focus_player=recent_eval.player if recent_eval else players.first()
    recent_performances=MatchPerformance.objects.select_related("player","match")[:6]
    return render(request,"core/dashboard.html",{
        "upcoming":upcoming,"next_training":next_training,"players_count":players.count(),"status_counts":status_counts,"injured_recovery":status_counts.get("injured",0)+status_counts.get("recovery",0),"averages":avg,"focus_player":focus_player,"recent_performances":recent_performances,
    })

@login_required
def player_list(request):
    q=request.GET.get("q","").strip()
    players=Player.objects.filter(active=True)
    if q: players=players.filter(Q(first_name__icontains=q)|Q(last_name__icontains=q)|Q(position__icontains=q)|Q(shirt_number__icontains=q))
    players=players.annotate(avg_performance=Avg("evaluations__performance"),avg_mentality=Avg("evaluations__mentality"),avg_physicality=Avg("evaluations__physicality"))
    return render(request,"core/player_list.html",{"players":players,"q":q})

@login_required
def player_create(request):
    form=PlayerForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        player=form.save(); messages.success(request,"Spieler wurde angelegt."); return redirect("player_detail",pk=player.pk)
    return render(request,"core/form_page.html",{"form":form,"title":"Spieler hinzufügen","eyebrow":"Kader","submit_label":"Spieler speichern","cancel_url":"players"})

@login_required
def player_detail(request,pk):
    player=get_object_or_404(Player,pk=pk)
    evaluations=player.evaluations.all()[:8]
    averages=player.evaluations.aggregate(mentality=Avg("mentality"),physicality=Avg("physicality"),performance=Avg("performance"),potential=Avg("potential"))
    matches=player.match_performances.select_related("match")[:8]
    return render(request,"core/player_detail.html",{"player":player,"evaluations":evaluations,"averages":averages,"matches":matches})

@login_required
def evaluate_player(request,pk):
    player=get_object_or_404(Player,pk=pk)
    initial={"mentality":7,"physicality":7,"performance":7,"potential":7}
    form=EvaluationForm(request.POST or None,initial=initial)
    if request.method=="POST" and form.is_valid():
        obj=form.save(commit=False); obj.player=player; obj.coach=request.user; obj.save()
        messages.success(request,f"Bewertung für {player.full_name} gespeichert."); return redirect("player_detail",pk=pk)
    return render(request,"core/evaluate.html",{"form":form,"player":player})

@login_required
def training_list(request):
    return render(request,"core/training_list.html",{"trainings":TrainingSession.objects.all()})

@login_required
def training_create(request):
    initial={"starts_at":timezone.localtime()+timedelta(days=1),"ends_at":timezone.localtime()+timedelta(days=1,hours=2)}
    form=TrainingForm(request.POST or None,initial=initial)
    if request.method=="POST" and form.is_valid():
        training=form.save(commit=False); training.created_by=request.user; training.save()
        for p in Player.objects.filter(active=True): Attendance.objects.get_or_create(training=training,player=p)
        TeamEvent.objects.create(title=training.title,event_type="training",starts_at=training.starts_at,ends_at=training.ends_at,location=training.location,notes=training.focus,created_by=request.user)
        messages.success(request,"Training wurde geplant."); return redirect("training_detail",pk=training.pk)
    return render(request,"core/form_page.html",{"form":form,"title":"Training planen","eyebrow":"Einfacher Ablauf","submit_label":"Training anlegen","cancel_url":"trainings"})

@login_required
def training_detail(request,pk):
    training=get_object_or_404(TrainingSession,pk=pk)
    task_form=TaskForm(request.POST or None)
    if request.method=="POST":
        action=request.POST.get("action")
        if action=="attendance":
            attendance=get_object_or_404(Attendance,pk=request.POST.get("attendance_id"),training=training)
            attendance.status=request.POST.get("status",attendance.status); attendance.save(update_fields=["status"])
            return JsonResponse({"ok":True,"label":attendance.get_status_display()})
        if action=="task" and task_form.is_valid():
            task=task_form.save(commit=False); task.training=training; task.save(); messages.success(request,"Aufgabe zugewiesen."); return redirect("training_detail",pk=pk)
        if action=="task_toggle":
            task=get_object_or_404(TaskAssignment,pk=request.POST.get("task_id"),training=training); task.completed=not task.completed; task.save(update_fields=["completed"]); return redirect("training_detail",pk=pk)
    attendance=training.attendance.select_related("player")
    stats={s:attendance.filter(status=s).count() for s,_ in Attendance.Status.choices}
    return render(request,"core/training_detail.html",{"training":training,"attendance":attendance,"stats":stats,"task_form":task_form})

@login_required
def calendar_view(request):
    today=timezone.localdate()
    try: year=int(request.GET.get("year",today.year)); month=int(request.GET.get("month",today.month))
    except ValueError: year,month=today.year,today.month
    cal=calendar.Calendar(firstweekday=0)
    weeks=[]
    start=timezone.make_aware(timezone.datetime(year,month,1))
    if month==12: end=timezone.make_aware(timezone.datetime(year+1,1,1))
    else: end=timezone.make_aware(timezone.datetime(year,month+1,1))
    events=list(TeamEvent.objects.filter(starts_at__gte=start,starts_at__lt=end))
    by_day={}
    for event in events: by_day.setdefault(timezone.localtime(event.starts_at).day,[]).append(event)
    for week in cal.monthdayscalendar(year,month): weeks.append([{"day":d,"events":by_day.get(d,[])} for d in week])
    prev_month=month-1 or 12; prev_year=year-1 if month==1 else year
    next_month=month+1 if month<12 else 1; next_year=year+1 if month==12 else year
    return render(request,"core/calendar.html",{"weeks":weeks,"month_name":["", "Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"][month],"month":month,"year":year,"prev_month":prev_month,"prev_year":prev_year,"next_month":next_month,"next_year":next_year})

@login_required
def event_create(request):
    form=EventForm(request.POST or None,initial={"starts_at":timezone.localtime()+timedelta(days=1)})
    if request.method=="POST" and form.is_valid():
        event=form.save(commit=False); event.created_by=request.user; event.save(); messages.success(request,"Termin wurde gespeichert."); return redirect("calendar")
    return render(request,"core/form_page.html",{"form":form,"title":"Termin hinzufügen","eyebrow":"Interner Kalender","submit_label":"Termin speichern","cancel_url":"calendar"})

@login_required
def match_list(request):
    return render(request,"core/match_list.html",{"matches":Match.objects.all()})

@login_required
def match_create(request):
    form=MatchForm(request.POST or None,initial={"kickoff":timezone.localtime()+timedelta(days=7)})
    if request.method=="POST" and form.is_valid():
        match=form.save(commit=False); match.created_by=request.user; match.save()
        TeamEvent.objects.create(title=f"vs. {match.opponent}",event_type="match",starts_at=match.kickoff,location=match.location,created_by=request.user)
        messages.success(request,"Spiel wurde angelegt."); return redirect("match_detail",pk=match.pk)
    return render(request,"core/form_page.html",{"form":form,"title":"Spiel anlegen","eyebrow":"Einzelspiel","submit_label":"Spiel speichern","cancel_url":"matches"})

@login_required
def match_detail(request,pk):
    match=get_object_or_404(Match,pk=pk)
    form=MatchPerformanceForm(request.POST or None)
    if request.method=="POST" and form.is_valid():
        perf=form.save(commit=False); perf.match=match
        MatchPerformance.objects.update_or_create(match=match,player=perf.player,defaults={"minutes_played":perf.minutes_played,"mentality":perf.mentality,"physicality":perf.physicality,"performance":perf.performance,"comment":perf.comment})
        messages.success(request,"Spielerleistung gespeichert."); return redirect("match_detail",pk=pk)
    return render(request,"core/match_detail.html",{"match":match,"performances":match.performances.select_related("player"),"form":form})

@login_required
def report(request):
    note=ReportNote.objects.first() or ReportNote.objects.create(updated_by=request.user)
    form=ReportNoteForm(request.POST or None,instance=note)
    if request.method=="POST" and form.is_valid():
        note=form.save(commit=False); note.updated_by=request.user; note.save(); messages.success(request,"Report-Kommentar gespeichert."); return redirect("report")
    latest_match=Match.objects.first(); recent_training=TrainingSession.objects.all()[:5]
    team_avg=PlayerEvaluation.objects.aggregate(mentality=Avg("mentality"),physicality=Avg("physicality"),performance=Avg("performance"))
    return render(request,"core/report.html",{"note_form":form,"note":note,"latest_match":latest_match,"recent_training":recent_training,"team_avg":team_avg})
