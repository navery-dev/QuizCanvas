from django.contrib import admin
from .models import Users, File, Quiz, Section, Question, QuizAttempt, Answer, Progress


@admin.register(Users)
class UsersAdmin(admin.ModelAdmin):
    list_display = ['userID', 'userName', 'email', 'dateJoined']
    list_filter = ['dateJoined']
    search_fields = ['userName', 'email']
    readonly_fields = ['userID', 'dateJoined']
    
    fieldsets = (
        ('User Information', {
            'fields': ('userName', 'email', 'password')
        }),
        ('System Generated', {
            'fields': ('userID', 'dateJoined'),
            'classes': ('collapse',)
        }),
    )


@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ['fileID', 'fileName', 'userID', 'fileType', 'uploadDate']
    list_filter = ['fileType', 'uploadDate']
    search_fields = ['fileName', 'userID__userName']
    readonly_fields = ['fileID', 'uploadDate', 'filePath']


@admin.register(Quiz) 
class QuizAdmin(admin.ModelAdmin):
    list_display = ['quizID', 'title', 'fileID', 'description']
    search_fields = ['title', 'fileID__fileName']
    readonly_fields = ['quizID']


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['sectionID', 'sectionName', 'quizID', 'sectionDesc']
    list_filter = ['quizID']
    search_fields = ['sectionName', 'quizID__title']
    readonly_fields = ['sectionID']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['questionID', 'questionText_short', 'quizID', 'sectionID', 'answerIndex']
    list_filter = ['quizID', 'sectionID']
    search_fields = ['questionText', 'quizID__title']
    readonly_fields = ['questionID']
    
    def questionText_short(self, obj):
        return obj.questionText[:50] + "..." if len(obj.questionText) > 50 else obj.questionText
    questionText_short.short_description = 'Question Text'


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['attemptID', 'userID', 'quizID', 'completed', 'score', 'startTime', 'endTime']
    list_filter = ['completed', 'startTime', 'quizID']
    search_fields = ['userID__userName', 'quizID__title']
    readonly_fields = ['attemptID', 'startTime']


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['userAnswerID', 'attemptID_user', 'questionID_short', 'selectedOption', 'isCorrect', 'responseTime']
    list_filter = ['isCorrect', 'attemptID__quizID']
    readonly_fields = ['userAnswerID', 'isCorrect']
    
    def attemptID_user(self, obj):
        return obj.attemptID.userID.userName
    attemptID_user.short_description = 'User'
    
    def questionID_short(self, obj):
        return obj.questionID.questionText[:30] + "..."
    questionID_short.short_description = 'Question'


@admin.register(Progress)
class ProgressAdmin(admin.ModelAdmin):
    list_display = ['progressID', 'userID', 'quizID', 'sectionID', 'masteryLevel', 'bestScore', 'attemptsCount', 'lastAttemptDate']
    list_filter = ['masteryLevel', 'quizID', 'lastAttemptDate']
    search_fields = ['userID__userName', 'quizID__title']
    readonly_fields = ['progressID']

