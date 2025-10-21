# 导入ROS2的Python客户端库
import rclpy
from rclpy.node import Node
# 导入我们将要发布的消息类型
from std_msgs.msg import String


class MyPublisher(Node):
    """
    创建一个继承自Node的类，作为我们的发布者节点
    """

    def __init__(self):
        # 调用父类的构造函数，并给节点命名为'my_publisher_node'
        super().__init__('my_publisher_node')
        # 创建一个发布者。
        # 参数1: 消息类型 (String)
        # 参数2: 话题名称 ('my_topic')
        # 参数3: 队列大小 (QoS, 保证服务质量的设置)
        self.publisher_ = self.create_publisher(String, 'my_topic', 10)

        # 创建一个定时器，每0.5秒调用一次timer_callback函数
        timer_period = 0.5  # seconds
        self.timer = self.create_timer(timer_period, self.timer_callback)

        # 创建一个计数器
        self.i = 0

    def timer_callback(self):
        # 这个函数在每次定时器触发时被调用
        msg = String()
        msg.data = f'Hello World: {self.i}'

        # 发布消息
        self.publisher_.publish(msg)

        # 在终端打印日志，确认消息已发出
        self.get_logger().info(f'Publishing: "{msg.data}"')

        # 计数器自增
        self.i += 1


def main(args=None):
    # 初始化rclpy库
    rclpy.init(args=args)

    # 创建我们的发布者节点实例
    my_publisher = MyPublisher()

    # rclpy.spin() 会让节点持续运行，直到被外部中断 (如Ctrl+C)
    rclpy.spin(my_publisher)

    # 节点关闭时，销毁节点并关闭rclpy
    my_publisher.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()