from django.contrib import admin
from django.db.models import Count, Avg, Max
from django.utils.html import format_html
from .models import Users, File, Quiz, Section, Question, QuizAttempt, Answer, Progress


# ===== CUSTOM ADMIN SITE CONFIGURATION =====
admin.site.site_header = "QuizCanvas Administration"
admin.site.site_title = "QuizCanvas Admin Portal"
admin.site.index_title = "Welcome to QuizCanvas Dashboard"


# ===== USERS ADMIN =====
@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ['userID', 'userName', 'email', 'dateJoined', 'quiz_count', 'total_attempts', 'avg_score']
    list_filter = ['dateJoined']
    search_fields = ['userName', 'email']
    readonly_fields = ['userID', 'dateJoined']
    date_hierarchy = 'dateJoined'
    
    fieldsets = (
        ('User Information', {
            'fields': ('userName', 'email', 'password')
        }),
        ('Statistics', {
            'fields': ('userID', 'dateJoined'),
            'classes': ('collapse',)
        }),
    )
    
    def quiz_count(self, obj):
        count = Quiz.objects.filter(fileID__userID=obj).count()
        return format_html('<span style="font-weight: bold; color: #3498db;">{}</span>', count)
    quiz_count.short_description = 'Quizzes Created'
    
    def total_attempts(self, obj):
        count = QuizAttempt.objects.filter(userID=obj).count()
        return format_html('<span style="font-weight: bold; color: #27ae60;">{}</span>', count)
    total_attempts.short_description = 'Total Attempts'
    
    def avg_score(self, obj):
        avg = QuizAttempt.objects.filter(
            userID=obj, 
            completed=True
        ).aggregate(Avg('score'))['score__avg']
        
        if avg is None:
            return format_html('<span style="color: #95a5a6;">N/A</span>')
        
        color = '#27ae60' if avg >= 80 else '#f39c12' if avg >= 60 else '#e74c3c'
        return format_html(
            '<span style="font-weight: bold; color: {};">{:.1f}%</span>',
            color, avg
        )
    avg_score.short_description = 'Average Score'


# ===== FILE ADMIN =====
@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ['fileID', 'fileName', 'get_owner', 'fileType', 'uploadDate']
    list_filter = ['fileType', 'uploadDate']
    search_fields = ['fileName', 'userID__userName']
    readonly_fields = ['fileID', 'uploadDate', 'filePath']
    date_hierarchy = 'uploadDate'
    
    def get_owner(self, obj):
        return obj.userID.userName
    get_owner.short_description = 'Owner'


# ===== QUIZ ADMIN =====
@admin.register(Quiz) 
class QuizAdmin(admin.ModelAdmin):
    list_display = ['quizID', 'title', 'get_owner', 'question_count', 'attempt_count', 'avg_score']
    list_filter = ['fileID__userID', 'fileID__uploadDate']
    search_fields = ['title', 'description', 'fileID__fileName']
    readonly_fields = ['quizID']
    
    def get_owner(self, obj):
        return obj.fileID.userID.userName
    get_owner.short_description = 'Owner'
    
    def question_count(self, obj):
        count = Question.objects.filter(quizID=obj).count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    question_count.short_description = 'Questions'
    
    def attempt_count(self, obj):
        count = QuizAttempt.objects.filter(quizID=obj, completed=True).count()
        return format_html('<span style="font-weight: bold; color: #3498db;">{}</span>', count)
    attempt_count.short_description = 'Completed'
    
    def avg_score(self, obj):
        avg = QuizAttempt.objects.filter(
            quizID=obj, 
            completed=True
        ).aggregate(Avg('score'))['score__avg']
        
        if avg is None:
            return format_html('<span style="color: #95a5a6;">No attempts</span>')
        
        color = '#27ae60' if avg >= 80 else '#f39c12' if avg >= 60 else '#e74c3c'
        return format_html(
            '<span style="font-weight: bold; color: {};">{:.1f}%</span>',
            color, avg
        )
    avg_score.short_description = 'Avg Score'


# ===== SECTION ADMIN =====
@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['sectionID', 'sectionName', 'get_quiz', 'question_count']
    list_filter = ['quizID']
    search_fields = ['sectionName', 'quizID__title']
    readonly_fields = ['sectionID']
    
    def get_quiz(self, obj):
        return obj.quizID.title
    get_quiz.short_description = 'Quiz'
    
    def question_count(self, obj):
        count = Question.objects.filter(sectionID=obj).count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)
    question_count.short_description = 'Questions'


# ===== QUESTION ADMIN =====
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['questionID', 'questionText_short', 'get_quiz', 'get_section', 'answerIndex']
    list_filter = ['quizID', 'sectionID']
    search_fields = ['questionText', 'quizID__title']
    readonly_fields = ['questionID']
    
    def questionText_short(self, obj):
        return obj.questionText[:50] + "..." if len(obj.questionText) > 50 else obj.questionText
    questionText_short.short_description = 'Question'
    
    def get_quiz(self, obj):
        return obj.quizID.title
    get_quiz.short_description = 'Quiz'
    
    def get_section(self, obj):
        return obj.sectionID.sectionName if obj.sectionID else 'N/A'
    get_section.short_description = 'Section'


# ===== QUIZ ATTEMPT ADMIN =====
@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['attemptID', 'get_user', 'get_quiz', 'completed', 'score_display', 'startTime', 'duration']
    list_filter = ['completed', 'startTime', 'quizID']
    search_fields = ['userID__userName', 'quizID__title']
    readonly_fields = ['attemptID', 'startTime']
    date_hierarchy = 'startTime'
    
    def get_user(self, obj):
        return obj.userID.userName
    get_user.short_description = 'User'
    
    def get_quiz(self, obj):
        return obj.quizID.title[:30] + "..." if len(obj.quizID.title) > 30 else obj.quizID.title
    get_quiz.short_description = 'Quiz'
    
    def score_display(self, obj):
        if obj.score is None:
            return format_html('<span style="color: #95a5a6;">-</span>')
        
        if obj.score >= 90:
            color = '#27ae60'
        elif obj.score >= 70:
            color = '#f39c12'
        else:
            color = '#e74c3c'
            
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, obj.score
        )
    score_display.short_description = 'Score'
    
    def duration(self, obj):
        if obj.endTime and obj.startTime:
            duration = obj.endTime - obj.startTime
            minutes = int(duration.total_seconds() / 60)
            seconds = int(duration.total_seconds() % 60)
            return f"{minutes}m {seconds}s"
        return format_html('<span style="color: #f39c12;">In Progress</span>')
    duration.short_description = 'Duration'


# ===== ANSWER ADMIN =====
@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['userAnswerID', 'get_user', 'questionID_short', 'selectedOption', 'correct_display', 'responseTime_display']
    list_filter = ['isCorrect', 'attemptID__quizID']
    readonly_fields = ['userAnswerID', 'isCorrect']
    
    def get_user(self, obj):
        return obj.attemptID.userID.userName
    get_user.short_description = 'User'
    
    def questionID_short(self, obj):
        return obj.questionID.questionText[:30] + "..."
    questionID_short.short_description = 'Question'
    
    def correct_display(self, obj):
        if obj.isCorrect:
            return format_html('<span style="color: #27ae60; font-weight: bold;">✓ Correct</span>')
        return format_html('<span style="color: #e74c3c; font-weight: bold;">✗ Incorrect</span>')
    correct_display.short_description = 'Result'
    
    def responseTime_display(self, obj):
        seconds = obj.responseTime / 1000 if obj.responseTime else 0
        return f"{seconds:.1f}s"
    responseTime_display.short_description = 'Time'


# ===== PROGRESS ADMIN =====
@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ['progressID', 'get_user', 'get_quiz', 'masteryLevel_colored', 'bestScore_display', 'attemptsCount', 'lastAttemptDate']
    list_filter = ['masteryLevel', 'quizID', 'lastAttemptDate']
    search_fields = ['userID__userName', 'quizID__title']
    readonly_fields = ['progressID']
    date_hierarchy = 'lastAttemptDate'
    
    def get_user(self, obj):
        return obj.userID.userName
    get_user.short_description = 'User'
    
    def get_quiz(self, obj):
        return obj.quizID.title[:30] + "..." if len(obj.quizID.title) > 30 else obj.quizID.title
    get_quiz.short_description = 'Quiz'
    
    def masteryLevel_colored(self, obj):
        colors = {
            'Expert': '#27ae60',
            'Advanced': '#3498db',
            'Intermediate': '#f39c12',
            'Beginner': '#e67e22',
            'Needs Practice': '#e74c3c'
        }
        color = colors.get(obj.masteryLevel, '#95a5a6')
        return format_html(
            '<span style="color: {}; font-weight: bold; font-size: 1.1em;">●</span> <span style="color: {};">{}</span>',
            color, color, obj.masteryLevel
        )
    masteryLevel_colored.short_description = 'Mastery Level'
    
    def bestScore_display(self, obj):
        color = '#27ae60' if obj.bestScore >= 80 else '#f39c12' if obj.bestScore >= 60 else '#e74c3c'
        return format_html(
            '<span style="font-weight: bold; color: {};">{:.1f}%</span>',
            color, obj.bestScore
        )
    bestScore_display.short_description = 'Best Score'