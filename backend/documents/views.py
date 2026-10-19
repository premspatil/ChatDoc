from django.core.files.base import ContentFile
from django.db import IntegrityError
from rest_framework import generics, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Document
from .serializers import DocumentSerializer, DocumentUploadSerializer
from .services import process_document, sha256_of, validate_upload


class DocumentListView(generics.ListAPIView):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        return Document.objects.filter(owner=self.request.user)  # only MY documents


class DocumentDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = DocumentSerializer

    def get_queryset(self):
        # Another user's id simply gives 404 - we do not even confirm it exists.
        return Document.objects.filter(owner=self.request.user)


class DocumentUploadView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "upload"

    def post(self, request):
        upload = DocumentUploadSerializer(data=request.data)
        upload.is_valid(raise_exception=True)
        uploaded_file = upload.validated_data["file"]

        data, page_count = validate_upload(uploaded_file)
        file_hash = sha256_of(data)

        existing = Document.objects.filter(owner=request.user, file_hash=file_hash).first()
        if existing:
            if existing.status != Document.Status.FAILED:
                # Same PDF already uploaded: reuse it instead of processing it again.
                body = DocumentSerializer(existing).data
                return Response({**body, "duplicate": True}, status=status.HTTP_200_OK)
            existing.delete()  # previous attempt failed, so start fresh

        document = Document(
            owner=request.user,
            original_filename=uploaded_file.name[:255],
            file_hash=file_hash,
            file_size=len(data),
            page_count=page_count,
        )
        document.file.save("upload.pdf", ContentFile(data), save=False)  # name is replaced by upload_path
        try:
            document.save()
        except IntegrityError:
            document.file.delete(save=False)
            return Response({"error": "This PDF was just uploaded."}, status=status.HTTP_409_CONFLICT)

        process_document(document)
        return Response(DocumentSerializer(document).data, status=status.HTTP_201_CREATED)
