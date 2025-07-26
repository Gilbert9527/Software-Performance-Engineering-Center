import json
import html
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from services.siliconflow_client import AnalysisResult


@dataclass
class Report:
    """Analysis report data structure"""
    id: str
    file_info: Dict[str, Any]
    analysis: Dict[str, Any]
    metadata: Dict[str, Any]
    created_at: datetime
    status: str


class ReportGenerator:
    """Generate formatted analysis reports"""
    
    def __init__(self):
        self.report_templates = {
            'html': self._get_html_template(),
            'json': self._get_json_template()
        }
    
    def generate_report(self, analysis_result: AnalysisResult, file_metadata: Dict[str, Any], 
                       analysis_id: str = None) -> Report:
        """
        Generate a structured report from analysis result
        
        Args:
            analysis_result: Result from SiliconFlow API
            file_metadata: Metadata about the analyzed file
            analysis_id: Unique identifier for this analysis
            
        Returns:
            Report object with structured data
        """
        if not analysis_id:
            import uuid
            analysis_id = str(uuid.uuid4())
        
        # Build file info section
        file_info = {
            'filename': file_metadata.get('filename', 'Unknown'),
            'file_type': file_metadata.get('file_type', 'Unknown'),
            'file_size': file_metadata.get('file_size', 0),
            'upload_time': file_metadata.get('upload_time', datetime.now().isoformat())
        }
        
        # Build analysis section
        analysis_data = {
            'content': analysis_result.content if analysis_result.success else '',
            'success': analysis_result.success,
            'error_message': analysis_result.error_message,
            'processing_time': analysis_result.processing_time,
            'model_used': analysis_result.model_used,
            'tokens_used': analysis_result.tokens_used,
            'prompt_used': file_metadata.get('prompt_used', '默认分析提示'),
            'created_at': datetime.now().isoformat()
        }
        
        # Build metadata section
        metadata = {
            'analysis_metadata': analysis_result.metadata or {},
            'file_metadata': file_metadata.get('extraction_metadata', {}),
            'generation_info': {
                'generator_version': '1.0',
                'generated_at': datetime.now().isoformat(),
                'report_format': 'structured'
            }
        }
        
        return Report(
            id=analysis_id,
            file_info=file_info,
            analysis=analysis_data,
            metadata=metadata,
            created_at=datetime.now(),
            status='completed' if analysis_result.success else 'failed'
        )
    
    def format_html_report(self, report: Report) -> str:
        """
        Format report as HTML
        
        Args:
            report: Report object to format
            
        Returns:
            HTML formatted report string
        """
        # Escape HTML content for security
        safe_content = html.escape(report.analysis['content']) if report.analysis['content'] else ''
        safe_filename = html.escape(report.file_info['filename'])
        
        # Format file size
        file_size = report.file_info['file_size']
        if file_size > 1024 * 1024:
            size_str = f"{file_size / (1024 * 1024):.1f} MB"
        elif file_size > 1024:
            size_str = f"{file_size / 1024:.1f} KB"
        else:
            size_str = f"{file_size} bytes"
        
        # Format processing time
        processing_time = report.analysis.get('processing_time', 0)
        time_str = f"{processing_time:.2f}秒" if processing_time else "未知"
        
        # Build status indicator
        if report.analysis['success']:
            status_class = "success"
            status_text = "分析成功"
            status_icon = "✓"
        else:
            status_class = "error"
            status_text = "分析失败"
            status_icon = "✗"
        
        # Format creation time
        created_at = datetime.fromisoformat(report.analysis['created_at'].replace('Z', '+00:00'))
        created_str = created_at.strftime('%Y年%m月%d日 %H:%M:%S')
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI分析报告 - {safe_filename}</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f5f5f5;
                }}
                .report-container {{
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .report-header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .report-title {{
                    font-size: 28px;
                    font-weight: 600;
                    margin: 0 0 10px 0;
                }}
                .report-subtitle {{
                    font-size: 16px;
                    opacity: 0.9;
                    margin: 0;
                }}
                .report-body {{
                    padding: 30px;
                }}
                .section {{
                    margin-bottom: 30px;
                    border-bottom: 1px solid #eee;
                    padding-bottom: 20px;
                }}
                .section:last-child {{
                    border-bottom: none;
                    margin-bottom: 0;
                }}
                .section-title {{
                    font-size: 20px;
                    font-weight: 600;
                    color: #2c3e50;
                    margin-bottom: 15px;
                    display: flex;
                    align-items: center;
                }}
                .section-title::before {{
                    content: '';
                    width: 4px;
                    height: 20px;
                    background: #667eea;
                    margin-right: 10px;
                    border-radius: 2px;
                }}
                .info-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 15px;
                    margin-bottom: 20px;
                }}
                .info-item {{
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 6px;
                    border-left: 3px solid #667eea;
                }}
                .info-label {{
                    font-weight: 600;
                    color: #495057;
                    font-size: 14px;
                    margin-bottom: 5px;
                }}
                .info-value {{
                    color: #212529;
                    font-size: 16px;
                }}
                .status-indicator {{
                    display: inline-flex;
                    align-items: center;
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-weight: 500;
                    font-size: 14px;
                }}
                .status-indicator.success {{
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }}
                .status-indicator.error {{
                    background: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }}
                .status-icon {{
                    margin-right: 6px;
                    font-weight: bold;
                }}
                .analysis-content {{
                    background: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 6px;
                    padding: 20px;
                    white-space: pre-wrap;
                    font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
                    font-size: 14px;
                    line-height: 1.5;
                    max-height: 600px;
                    overflow-y: auto;
                }}
                .error-message {{
                    background: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                    border-radius: 6px;
                    padding: 15px;
                    margin-top: 10px;
                }}
                .metadata-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }}
                .metadata-table th,
                .metadata-table td {{
                    padding: 8px 12px;
                    text-align: left;
                    border-bottom: 1px solid #dee2e6;
                }}
                .metadata-table th {{
                    background: #f8f9fa;
                    font-weight: 600;
                    color: #495057;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    background: #f8f9fa;
                    color: #6c757d;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="report-container">
                <div class="report-header">
                    <h1 class="report-title">AI文档分析报告</h1>
                    <p class="report-subtitle">基于SiliconFlow AI技术的智能文档分析</p>
                </div>
                
                <div class="report-body">
                    <!-- 文件信息部分 -->
                    <div class="section">
                        <h2 class="section-title">文件信息</h2>
                        <div class="info-grid">
                            <div class="info-item">
                                <div class="info-label">文件名称</div>
                                <div class="info-value">{safe_filename}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">文件类型</div>
                                <div class="info-value">{report.file_info['file_type'].upper()}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">文件大小</div>
                                <div class="info-value">{size_str}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">上传时间</div>
                                <div class="info-value">{report.file_info['upload_time']}</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 分析状态部分 -->
                    <div class="section">
                        <h2 class="section-title">分析状态</h2>
                        <div class="info-grid">
                            <div class="info-item">
                                <div class="info-label">分析状态</div>
                                <div class="info-value">
                                    <span class="status-indicator {status_class}">
                                        <span class="status-icon">{status_icon}</span>
                                        {status_text}
                                    </span>
                                </div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">处理时间</div>
                                <div class="info-value">{time_str}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">分析时间</div>
                                <div class="info-value">{created_str}</div>
                            </div>
                            <div class="info-item">
                                <div class="info-label">使用模型</div>
                                <div class="info-value">{report.analysis.get('model_used', '未知')}</div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- 分析结果部分 -->
                    <div class="section">
                        <h2 class="section-title">分析结果</h2>
                        {self._format_analysis_content(report)}
                    </div>
                    
                    <!-- 技术信息部分 -->
                    <div class="section">
                        <h2 class="section-title">技术信息</h2>
                        {self._format_technical_info(report)}
                    </div>
                </div>
                
                <div class="footer">
                    <p>报告生成时间: {datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')} | 
                       报告ID: {report.id}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def _format_analysis_content(self, report: Report) -> str:
        """Format the analysis content section"""
        if report.analysis['success']:
            content = report.analysis['content']
            return f'<div class="analysis-content">{html.escape(content)}</div>'
        else:
            error_msg = report.analysis.get('error_message', '未知错误')
            return f'<div class="error-message"><strong>分析失败:</strong> {html.escape(error_msg)}</div>'
    
    def _format_technical_info(self, report: Report) -> str:
        """Format the technical information section"""
        tokens_used = report.analysis.get('tokens_used', 0)
        tokens_str = f"{tokens_used} tokens" if tokens_used else "未知"
        
        prompt_used = report.analysis.get('prompt_used', '默认分析提示')
        
        return f"""
        <table class="metadata-table">
            <tr>
                <th>项目</th>
                <th>值</th>
            </tr>
            <tr>
                <td>使用的Token数量</td>
                <td>{tokens_str}</td>
            </tr>
            <tr>
                <td>分析提示词</td>
                <td>{html.escape(prompt_used)}</td>
            </tr>
            <tr>
                <td>报告格式版本</td>
                <td>{report.metadata['generation_info']['generator_version']}</td>
            </tr>
        </table>
        """
    
    def format_json_report(self, report: Report) -> Dict[str, Any]:
        """
        Format report as JSON
        
        Args:
            report: Report object to format
            
        Returns:
            Dictionary suitable for JSON serialization
        """
        return {
            'id': report.id,
            'file_info': report.file_info,
            'analysis': report.analysis,
            'metadata': report.metadata,
            'created_at': report.created_at.isoformat(),
            'status': report.status,
            'report_version': '1.0'
        }
    
    def format_summary_report(self, report: Report) -> Dict[str, Any]:
        """
        Format a summary version of the report
        
        Args:
            report: Report object to format
            
        Returns:
            Dictionary with summary information
        """
        # Extract key insights from analysis content
        content = report.analysis.get('content', '')
        summary = self._extract_summary(content) if content else '无分析内容'
        
        return {
            'id': report.id,
            'filename': report.file_info['filename'],
            'file_type': report.file_info['file_type'],
            'status': report.status,
            'success': report.analysis['success'],
            'summary': summary,
            'processing_time': report.analysis.get('processing_time', 0),
            'created_at': report.created_at.isoformat(),
            'tokens_used': report.analysis.get('tokens_used', 0)
        }
    
    def _extract_summary(self, content: str, max_length: int = 200) -> str:
        """
        Extract a summary from analysis content
        
        Args:
            content: Full analysis content
            max_length: Maximum length of summary
            
        Returns:
            Summary string
        """
        if not content:
            return '无内容'
        
        # Try to find the first paragraph or sentence that looks like a summary
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line and len(line) > 20:  # Skip very short lines
                if len(line) <= max_length:
                    return line
                else:
                    # Truncate at word boundary
                    truncated = line[:max_length]
                    last_space = truncated.rfind(' ')
                    if last_space > max_length * 0.7:  # If we can find a reasonable break point
                        return truncated[:last_space] + '...'
                    else:
                        return truncated + '...'
        
        # Fallback: just truncate the content
        if len(content) <= max_length:
            return content.strip()
        else:
            truncated = content[:max_length]
            last_space = truncated.rfind(' ')
            if last_space > max_length * 0.7:
                return truncated[:last_space] + '...'
            else:
                return truncated + '...'
    
    def _get_html_template(self) -> str:
        """Get HTML template for reports"""
        return "html_template"  # Placeholder for template system
    
    def _get_json_template(self) -> str:
        """Get JSON template for reports"""
        return "json_template"  # Placeholder for template system
    
    def export_report(self, report: Report, format_type: str = 'json') -> str:
        """
        Export report in specified format
        
        Args:
            report: Report to export
            format_type: Export format ('json', 'html', 'summary')
            
        Returns:
            Formatted report string
        """
        if format_type == 'html':
            return self.format_html_report(report)
        elif format_type == 'json':
            return json.dumps(self.format_json_report(report), ensure_ascii=False, indent=2)
        elif format_type == 'summary':
            return json.dumps(self.format_summary_report(report), ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    def validate_report(self, report: Report) -> Dict[str, Any]:
        """
        Validate report structure and content
        
        Args:
            report: Report to validate
            
        Returns:
            Validation result dictionary
        """
        validation_result = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Check required fields
        if not report.id:
            validation_result['errors'].append("Report ID is missing")
            validation_result['valid'] = False
        
        if not report.file_info.get('filename'):
            validation_result['errors'].append("Filename is missing")
            validation_result['valid'] = False
        
        if not isinstance(report.analysis.get('success'), bool):
            validation_result['errors'].append("Analysis success status is missing or invalid")
            validation_result['valid'] = False
        
        # Check content based on success status
        if report.analysis.get('success'):
            if not report.analysis.get('content'):
                validation_result['warnings'].append("Analysis succeeded but content is empty")
        else:
            if not report.analysis.get('error_message'):
                validation_result['warnings'].append("Analysis failed but no error message provided")
        
        # Check processing time
        processing_time = report.analysis.get('processing_time')
        if processing_time is not None and processing_time < 0:
            validation_result['warnings'].append("Processing time is negative")
        
        return validation_result