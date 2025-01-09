# serializers.py
from rest_framework import serializers
from .models import Bus, Book, User

class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = '__all__'

class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            "id",
            "busid",
            "nos",
            "bus_name",
            "source",
            "dest",
            "price",
            "date",
            "time",
            "status",
            "userid",
            "name",
            "email"
        ]
        read_only_fields = ["id", "status", "userid", "name", "email", "bus_name", "source", "dest", "price", "date", "time"]

    def create(self, validated_data):
        # Fetch the Bus instance using the provided busid
        bus_id = validated_data.get('busid')
        try:
            bus = Bus.objects.get(id=bus_id)
        except Bus.DoesNotExist:
            raise serializers.ValidationError({"busid": "Invalid bus ID"})

        # Populate fields from the Bus instance
        validated_data['bus_name'] = bus.bus_name
        validated_data['source'] = bus.source
        validated_data['dest'] = bus.dest
        validated_data['price'] = bus.price
        validated_data['date'] = bus.date
        validated_data['time'] = bus.time

        # Populate user-related fields
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['userid'] = request.user.id
            validated_data['name'] = request.user.username
            validated_data['email'] = request.user.email

        # Save the booking
        return super().create(validated_data)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'name', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['name'],
            password=validated_data['password']
        )
        return user