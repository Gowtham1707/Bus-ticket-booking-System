# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import BusSerializer, BookSerializer, UserSerializer
from .models import Bus, Book
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from .serializers import UserSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class BusViewSet(viewsets.ModelViewSet):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Bus.objects.all()
        source = self.request.query_params.get('source', None)
        dest = self.request.query_params.get('destination', None)
        date = self.request.query_params.get('date', None)
        
        if source and dest and date:
            queryset = queryset.filter(source=source, dest=dest, date=date)
        return queryset

# class BookViewSet(viewsets.ModelViewSet):
#     serializer_class = BookSerializer
#     permission_classes = [IsAuthenticated]

#     def get_queryset(self):
#         return Book.objects.filter(userid=self.request.user.id)

#     def create(self, request):
#         bus = Bus.objects.get(id=request.data['busid'])
#         if bus.rem >= int(request.data['nos']):
#             # Update remaining seats
#             bus.rem -= int(request.data['nos'])
#             bus.save()
            
#             # Create booking
#             serializer = self.get_serializer(data=request.data)
#             serializer.is_valid(raise_exception=True)
#             serializer.save()
            
#             return Response(serializer.data, status=status.HTTP_201_CREATED)
#         return Response(
#             {"error": "Not enough seats available"},
#             status=status.HTTP_400_BAD_REQUEST
#         )

class BookViewSet(viewsets.ModelViewSet):
    serializer_class = BookSerializer
    permission_classes = [IsAuthenticated]

    # def get_queryset(self):
    #     return Book.objects.filter(userid=self.request.user.id)

    def get_queryset(self):
        # Exclude cancelled bookings
        return Book.objects.filter(userid=self.request.user.id, status='B')

    def create(self, request, *args, **kwargs):
        try:
            bus_id = request.data.get('busid')
            num_seats = int(request.data.get('nos'))

            # Check if the bus exists
            bus = Bus.objects.get(id=bus_id)
            if bus.rem < num_seats:
                return Response(
                    {"error": "Not enough seats available"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Update the remaining seats
            bus.rem -= num_seats
            bus.save()

            # Prepare booking data
            booking_data = {
                "busid": bus_id,
                "bus_name": bus.bus_name,
                "source": bus.source,
                "dest": bus.dest,
                "price": bus.price,
                "nos": num_seats,
                "date": bus.date,
                "time": bus.time,
                "status": "BOOKED",
                "userid": request.user.id,
                "name": request.user.username,
                "email": request.user.email,
            }

            # Serialize and save the booking
            serializer = self.get_serializer(data=booking_data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Bus.DoesNotExist:
            return Response(
                {"error": "Bus not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError as e:
            return Response(
                {"error": f"Invalid data: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

@api_view(['POST'])
def cancel_booking(request, booking_id):
    try:
        booking = Book.objects.get(id=booking_id, userid=request.user.id)
        bus = Bus.objects.get(id=booking.busid)
        
        # Update remaining seats
        bus.rem += booking.nos
        bus.save()
        
        # Update booking status
        booking.status = 'CANCELLED'
        booking.nos = 0
        booking.save()
        
        return Response({"message": "Booking cancelled successfully"})
    except Book.DoesNotExist:
        return Response(
            {"error": "Booking not found"},
            status=status.HTTP_404_NOT_FOUND
        )