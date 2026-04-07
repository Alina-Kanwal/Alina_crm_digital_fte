"""
Executive summary generation service for daily reports.
Creates concise executive summaries for support managers.
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ExecutiveSummaryGenerator:
    """
    Service for generating executive summaries from daily reports.

    Provides:
    - Key metrics at a glance
    - Trend analysis (improving/declining)
    - Action items and recommendations
    - Top issues requiring attention
    """

    def __init__(self):
        """Initialize executive summary generator."""
        self.max_summary_length = 500  # Characters limit
        self.max_issues = 5  # Number of top issues to highlight
        logger.info("Executive summary generator initialized")

    async def generate_executive_summary(
        self,
        daily_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate executive summary from daily report data.

        Args:
            daily_report: Full daily report dictionary

        Returns:
            Dictionary containing executive summary
        """
        try:
            sentiment_summary = daily_report.get('sentiment_summary', {})
            ticket_summary = daily_report.get('ticket_summary', {})
            top_complaints = daily_report.get('top_complaints', [])
            trend_analysis = daily_report.get('trend_analysis', {})

            # Generate key highlights
            highlights = self._generate_highlights(
                sentiment_summary,
                ticket_summary,
                trend_analysis
            )

            # Generate action items
            action_items = self._generate_action_items(
                sentiment_summary,
                ticket_summary,
                top_complaints,
                trend_analysis
            )

            # Generate risk assessment
            risk_assessment = self._assess_risks(
                sentiment_summary,
                ticket_summary,
                trend_analysis
            )

            # Build summary text
            summary_text = self._build_summary_text(
                highlights,
                action_items,
                risk_assessment
            )

            executive_summary = {
                'report_date': daily_report.get('report_date'),
                'generated_at': datetime.now().isoformat(),
                'highlights': highlights,
                'action_items': action_items,
                'risk_assessment': risk_assessment,
                'summary_text': summary_text,
                'overall_score': self._calculate_overall_score(
                    sentiment_summary,
                    ticket_summary
                )
            }

            logger.info("Executive summary generated")

            return executive_summary

        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return {
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }

    def _generate_highlights(
        self,
        sentiment_summary: Dict[str, Any],
        ticket_summary: Dict[str, Any],
        trend_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate key highlights from report data.

        Args:
            sentiment_summary: Sentiment statistics
            ticket_summary: Ticket statistics
            trend_analysis: Trend analysis data

        Returns:
            List of highlight dictionaries
        """
        highlights = []

        # Ticket volume highlight
        total_tickets = ticket_summary.get('total_tickets', 0)
        highlights.append({
            'type': 'volume',
            'text': f"Processed {total_tickets} support tickets",
            'value': total_tickets,
            'trend': 'up' if total_tickets > 50 else 'down' if total_tickets < 30 else 'stable'
        })

        # Resolution rate highlight
        resolution_rate = ticket_summary.get('resolution_rate', 0)
        if resolution_rate > 80:
            highlights.append({
                'type': 'performance',
                'text': f"Strong resolution rate: {resolution_rate:.1f}%",
                'value': resolution_rate,
                'status': 'positive'
            })
        elif resolution_rate < 60:
            highlights.append({
                'type': 'performance',
                'text': f"Low resolution rate: {resolution_rate:.1f}%",
                'value': resolution_rate,
                'status': 'negative'
            })

        # Sentiment highlight
        net_sentiment = sentiment_summary.get('net_sentiment', 'neutral')
        if net_sentiment == 'positive':
            highlights.append({
                'type': 'sentiment',
                'text': "Positive customer sentiment overall",
                'value': 'positive',
                'status': 'positive'
            })
        elif net_sentiment == 'negative':
            highlights.append({
                'type': 'sentiment',
                'text': "Negative customer sentiment requires attention",
                'value': 'negative',
                'status': 'negative'
            })

        # Trend highlight
        sentiment_trend = trend_analysis.get('sentiment_trend', 'stable')
        if sentiment_trend != 'stable':
            highlights.append({
                'type': 'trend',
                'text': f"Sentiment {sentiment_trend} over previous period",
                'value': sentiment_trend,
                'status': 'positive' if sentiment_trend == 'improving' else 'negative'
            })

        # Escalation rate highlight
        escalation_rate = ticket_summary.get('escalation_rate', 0)
        if escalation_rate > 20:
            highlights.append({
                'type': 'escalation',
                'text': f"Escalation rate {escalation_rate:.1f}% above 20% target",
                'value': escalation_rate,
                'status': 'negative'
            })
        elif escalation_rate < 15:
            highlights.append({
                'type': 'escalation',
                'text': f"Escalation rate {escalation_rate:.1f}% well below 20% target",
                'value': escalation_rate,
                'status': 'positive'
            })

        return highlights

    def _generate_action_items(
        self,
        sentiment_summary: Dict[str, Any],
        ticket_summary: Dict[str, Any],
        top_complaints: List[Dict[str, Any]],
        trend_analysis: Dict[str, Any]
    ) -> List[str]:
        """
        Generate action items from report data.

        Args:
            sentiment_summary: Sentiment statistics
            ticket_summary: Ticket statistics
            top_complaints: Top complaints list
            trend_analysis: Trend analysis

        Returns:
            List of action item strings
        """
        action_items = []

        # Resolution rate action
        resolution_rate = ticket_summary.get('resolution_rate', 0)
        if resolution_rate < 60:
            action_items.append(
                f"⚠️ Review AI agent responses - resolution rate ({resolution_rate:.1f}%) below 60%"
            )

        # Escalation rate action
        escalation_rate = ticket_summary.get('escalation_rate', 0)
        if escalation_rate > 20:
            action_items.append(
                f"⚠️ Investigate escalation triggers - rate ({escalation_rate:.1f}%) above 20% target"
            )

        # Negative sentiment action
        negative_pct = sentiment_summary.get('negative_percentage', 0)
        if negative_pct > 30:
            action_items.append(
                f"⚠️ Address high negative sentiment ({negative_pct:.1f}%) - review common complaints"
            )

        # Top complaint action
        if len(top_complaints) > 0:
            top_complaint = top_complaints[0]
            top_count = top_complaint.get('count', 0)
            if top_count > 5:
                action_items.append(
                    f"📈 Prioritize resolution for '{top_complaint.get('complaint')}' ({top_count} occurrences)"
                )

        # Trend action
        sentiment_trend = trend_analysis.get('sentiment_trend', 'stable')
        if sentiment_trend == 'declining':
            action_items.append(
                f"📉 Investigate recent changes causing sentiment decline"
            )
        elif sentiment_trend == 'improving':
            action_items.append(
                f"📈 Continue current approach - sentiment trend positive"
            )

        return action_items if action_items else ["✅ All metrics within acceptable ranges"]

    def _assess_risks(
        self,
        sentiment_summary: Dict[str, Any],
        ticket_summary: Dict[str, Any],
        trend_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Assess risks based on report data.

        Args:
            sentiment_summary: Sentiment statistics
            ticket_summary: Ticket statistics
            trend_analysis: Trend analysis data

        Returns:
            Dictionary containing risk assessment
        """
        risks = []

        # Resolution rate risk
        resolution_rate = ticket_summary.get('resolution_rate', 0)
        if resolution_rate < 50:
            risks.append({
                'type': 'critical',
                'description': f"Very low resolution rate ({resolution_rate:.1f}%) indicates major issues",
                'impact': 'high'
            })
        elif resolution_rate < 60:
            risks.append({
                'type': 'high',
                'description': f"Low resolution rate ({resolution_rate:.1f}%) requires investigation",
                'impact': 'medium'
            })

        # Negative sentiment risk
        negative_pct = sentiment_summary.get('negative_percentage', 0)
        if negative_pct > 40:
            risks.append({
                'type': 'high',
                'description': f"High negative sentiment ({negative_pct:.1f}%) affects customer satisfaction",
                'impact': 'medium'
            })
        elif negative_pct > 30:
            risks.append({
                'type': 'medium',
                'description': f"Elevated negative sentiment ({negative_pct:.1f}%) needs monitoring",
                'impact': 'low'
            })

        # Escalation rate risk
        escalation_rate = ticket_summary.get('escalation_rate', 0)
        if escalation_rate > 25:
            risks.append({
                'type': 'critical',
                'description': f"Escalation rate ({escalation_rate:.1f}%) severely above 20% target",
                'impact': 'critical'
            })
        elif escalation_rate > 20:
            risks.append({
                'type': 'high',
                'description': f"Escalation rate ({escalation_rate:.1f}%) exceeds 20% target",
                'impact': 'high'
            })

        # Trend risk
        sentiment_trend = trend_analysis.get('sentiment_trend', 'stable')
        if sentiment_trend == 'declining':
            risks.append({
                'type': 'high',
                'description': f"Sentiment trend is {sentiment_trend} - investigate causes",
                'impact': 'medium'
            })

        return {
            'has_risks': len(risks) > 0,
            'risk_count': len(risks),
            'risks': risks,
            'overall_risk_level': 'critical' if any(r['type'] == 'critical' for r in risks) else 'high' if any(r['type'] == 'high' for r in risks) else 'medium' if len(risks) > 0 else 'low'
        }

    def _build_summary_text(
        self,
        highlights: List[Dict[str, Any]],
        action_items: List[str],
        risk_assessment: Dict[str, Any]
    ) -> str:
        """
        Build executive summary text from components.

        Args:
            highlights: List of highlight dictionaries
            action_items: List of action item strings
            risk_assessment: Risk assessment dictionary

        Returns:
            Formatted executive summary text
        """
        summary_parts = []

        # Add highlights
        if highlights:
            summary_parts.append("**Key Highlights:**")
            for highlight in highlights[:5]:  # Top 5 highlights
                status_icon = "✅" if highlight['status'] == 'positive' else "⚠️" if highlight['status'] == 'negative' else "ℹ️"
                summary_parts.append(f"{status_icon} {highlight['text']}")

        # Add action items
        if action_items:
            summary_parts.append("\n**Action Items:**")
            for action in action_items[:5]:  # Top 5 actions
                summary_parts.append(action)

        # Add risk assessment
        if risk_assessment['has_risks']:
            risk_level = risk_assessment['overall_risk_level'].upper()
            summary_parts.append(f"\n**Risk Assessment:** {risk_level} - {len(risk_assessment['risks'])} risk(s) identified")

        # Combine
        full_summary = "\n".join(summary_parts)

        # Truncate if too long
        if len(full_summary) > self.max_summary_length:
            full_summary = full_summary[:self.max_summary_length] + "..."

        return full_summary

    def _calculate_overall_score(
        self,
        sentiment_summary: Dict[str, Any],
        ticket_summary: Dict[str, Any]
    ) -> float:
        """
        Calculate overall performance score (0-100).

        Args:
            sentiment_summary: Sentiment statistics
            ticket_summary: Ticket statistics

        Returns:
            Overall score (0-100)
        """
        score = 100.0  # Start at 100

        # Deduct for low resolution rate
        resolution_rate = ticket_summary.get('resolution_rate', 100)
        if resolution_rate < 50:
            score -= 30
        elif resolution_rate < 60:
            score -= 20
        elif resolution_rate < 70:
            score -= 10

        # Deduct for high negative sentiment
        negative_pct = sentiment_summary.get('negative_percentage', 0)
        if negative_pct > 40:
            score -= 30
        elif negative_pct > 30:
            score -= 20
        elif negative_pct > 20:
            score -= 10

        # Deduct for high escalation rate
        escalation_rate = ticket_summary.get('escalation_rate', 0)
        if escalation_rate > 25:
            score -= 30
        elif escalation_rate > 20:
            score -= 15

        # Ensure score is within bounds
        score = max(0.0, min(100.0, score))

        return score
