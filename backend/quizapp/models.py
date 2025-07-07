from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Users(models.Model):
    userID = models.AutoField(primary_key=True)
    userName = models.CharField(max_length=10, unique=True)
    email = models.EmailField(max_length=50, unique=True)
    password = models.CharField(max_length=128)
    dateJoined = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'
        verbose_name = "User"
        verbose_name_plural = "Users"
    
    def __str__(self):
        return self.userName
    
class File(models.Model):
    fileID = models.AutoField(primary_key=True)  # ID 6
    userID = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='userID', related_name='files')
    fileName = models.CharField(max_length=50)
    filePath = models.CharField(max_length=100)
    fileType = models.CharField(max_length=4)
    uploadDate = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'file'
        verbose_name = "File"
        verbose_name_plural = "Files"
        ordering = ['-uploadDate']
    
    def __str__(self):
        return f"{self.fileName} ({self.userID.userName})"

class Quiz(models.Model):
    quizID = models.AutoField(primary_key=True)
    fileID = models.ForeignKey(File, on_delete=models.CASCADE, db_column='fileID', related_name='quizzes')
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'quiz'
        verbose_name = "Quiz"
        verbose_name_plural = "Quizzes"
        ordering = ['-quizID']
    
    def __str__(self):
        return self.title
    
class Section(models.Model):
    sectionID = models.AutoField(primary_key=True)
    quizID = models.ForeignKey(Quiz, on_delete=models.CASCADE, db_column='quizID', related_name='sections')
    sectionName = models.CharField(max_length=50, blank=True, null=True)
    sectionDesc = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'section'
        verbose_name = "Section"
        verbose_name_plural = "Sections"
        ordering = ['quizID', 'sectionName']
    
    def __str__(self):
        quiz_title = self.quizID.title if self.quizID else "Unknown Quiz"
        section_name = self.sectionName if self.sectionName else "Unnamed Section"
        return f"{quiz_title} - {section_name}"
    
class Question(models.Model):
    questionID = models.AutoField(primary_key=True)
    quizID = models.ForeignKey(Quiz, on_delete=models.CASCADE, db_column='quizID', related_name='questions')
    sectionID = models.ForeignKey(Section, on_delete=models.CASCADE, db_column='sectionID', related_name='questions')  # ID 22
    questionText = models.CharField(max_length=500) 
    answerOptions = models.JSONField() 
    answerIndex = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)])

    class Meta:
        db_table = 'question'
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ['quizID', 'questionID']
    
    def __str__(self):
        return f"Q{self.questionID}: {self.questionText[:50]}..."
    
    @property
    def correctAnswer(self):
        if self.answerOptions and 0 <= self.answerIndex < len(self.answerOptions):
            return self.answerOptions[self.answerIndex]
        return None

class QuizAttempt(models.Model):
    attemptID = models.AutoField(primary_key=True)
    userID = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='userID', related_name='quizAttempts')
    quizID = models.ForeignKey(Quiz, on_delete=models.CASCADE, db_column='quizID', related_name='attempts')
    sectionID = models.ForeignKey(Section, on_delete=models.SET_NULL, db_column='sectionID', related_name='sectionAttempts', null=True, blank=True)
    startTime = models.DateTimeField(auto_now_add=True)
    endTime = models.DateTimeField(null=True, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,  
                               validators=[MinValueValidator(0.00), MaxValueValidator(100.00)])
    completed = models.BooleanField(default=False)

    class Meta:
        db_table = 'quizattempt'
        verbose_name = "Quiz Attempt"
        verbose_name_plural = "Quiz Attempts"
        ordering = ['-startTime']
    
    def __str__(self):
        return f"{self.userID.userName} - {self.quizID.title} ({self.startTime.date()})"
    
    def completeAttempt(self):
        self.completed = True
        self.endTime = timezone.now()
        self.save()

class Answer(models.Model):
    userAnswerID = models.AutoField(primary_key=True)
    attemptID = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, db_column='attemptID', related_name='answers')
    questionID = models.ForeignKey(Question, on_delete=models.CASCADE, db_column='questionID', related_name='userAnswers')
    selectedOption = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(99)])
    isCorrect = models.BooleanField()                  
    responseTime = models.IntegerField(null=True, blank=True,
                                     validators=[MinValueValidator(0), MaxValueValidator(99999)])

    class Meta:
        db_table = 'answer'
        verbose_name = "Answer"
        verbose_name_plural = "Answers"
        unique_together = ['attemptID', 'questionID']
    
    def __str__(self):
        return f"{self.attemptID.userID.userName} - Q{self.questionID.questionID}: {'Correct' if self.isCorrect else 'Incorrect'}"
    
    def save(self, *args, **kwargs):
        self.isCorrect = (self.selectedOption == self.questionID.answerIndex)
        super().save(*args, **kwargs)

class Progress(models.Model):
    MASTERY_CHOICES = [
        ('Not Started', 'Not Started'),
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Mastered', 'Mastered'),
    ]
    
    progressID = models.AutoField(primary_key=True)
    userID = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='userID', related_name='progress')
    quizID = models.ForeignKey(Quiz, on_delete=models.CASCADE, db_column='quizID', related_name='userProgress')
    sectionID = models.ForeignKey(Section, on_delete=models.CASCADE, db_column='sectionID', 
                                 related_name='userProgress', null=True, blank=True)
    attemptsCount = models.IntegerField(default=0,     
                                       validators=[MinValueValidator(0), MaxValueValidator(99999)])
    bestScore = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True,  
                                   validators=[MinValueValidator(0.00), MaxValueValidator(100.00)])
    lastAttemptDate = models.DateTimeField(null=True, blank=True)  
    masteryLevel = models.CharField(max_length=20, choices=MASTERY_CHOICES, default='Not Started')  

    class Meta:
        db_table = 'progress'
        verbose_name = "Progress"
        verbose_name_plural = "Progress Records"
        unique_together = ['userID', 'quizID', 'sectionID']
        ordering = ['-lastAttemptDate']
    
    def __str__(self):
        section_name = f" - {self.sectionID.sectionName}" if self.sectionID and self.sectionID.sectionName else ""
        return f"{self.userID.userName}: {self.quizID.title}{section_name} ({self.masteryLevel})"
    
    def updateProgress(self, newScore):
        """Update progress with new attempt data."""
        self.attemptsCount += 1
        if self.bestScore is None or newScore > self.bestScore:
            self.bestScore = newScore
        self.lastAttemptDate = timezone.now()
        self.save()