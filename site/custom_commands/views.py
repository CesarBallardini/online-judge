from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import AdminAPIKeyAuthentication
from .loader import load_problems, load_users, parse_csv
from .permissions import HasValidAPIKey


class BaseLoadView(APIView):
    """Base class for CSV upload endpoints."""

    authentication_classes = [AdminAPIKeyAuthentication]
    permission_classes = [HasValidAPIKey]
    parser_classes = [MultiPartParser, FormParser]

    def _read_csv(self, request):
        """Extract CSV content from the uploaded file."""
        csv_file = request.FILES.get('file')
        if not csv_file:
            return None, Response(
                {'error': 'No file uploaded. Send a CSV file as multipart field "file".'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            content = csv_file.read().decode('utf-8')
        except UnicodeDecodeError:
            return None, Response(
                {'error': 'File is not valid UTF-8.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        rows = parse_csv(content)
        if not rows:
            return None, Response(
                {'error': 'CSV file is empty or has no data rows.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return rows, None


class LoadStudentsView(BaseLoadView):
    """POST /api/admin/load-students/  --  Bulk-create student accounts from CSV."""

    def post(self, request):
        rows, err = self._read_csv(request)
        if err:
            return err

        dry_run = request.query_params.get('dry_run', '').lower() in ('1', 'true', 'yes')
        result = load_users(rows, is_teacher=False, dry_run=dry_run)
        return Response(result, status=status.HTTP_201_CREATED if result['created'] else status.HTTP_200_OK)


class LoadTeachersView(BaseLoadView):
    """POST /api/admin/load-teachers/  --  Bulk-create teacher accounts from CSV."""

    def post(self, request):
        rows, err = self._read_csv(request)
        if err:
            return err

        dry_run = request.query_params.get('dry_run', '').lower() in ('1', 'true', 'yes')
        result = load_users(rows, is_teacher=True, dry_run=dry_run)
        return Response(result, status=status.HTTP_201_CREATED if result['created'] else status.HTTP_200_OK)


class LoadProblemsView(BaseLoadView):
    """POST /api/admin/load-problems/  --  Bulk-create problems from CSV."""

    def post(self, request):
        rows, err = self._read_csv(request)
        if err:
            return err

        dry_run = request.query_params.get('dry_run', '').lower() in ('1', 'true', 'yes')
        result = load_problems(rows, dry_run=dry_run)
        return Response(result, status=status.HTTP_201_CREATED if result['created'] else status.HTTP_200_OK)
