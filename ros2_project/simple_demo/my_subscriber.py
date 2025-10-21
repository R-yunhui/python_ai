# 导入ROS2的Python客户端库
import rclpy
from rclpy.node import Node
# 导入我们将要订阅的消息类型
from std_msgs.msg import String


class MySubscriber(Node):
    """
    创建一个继承自Node的类，作为我们的订阅者节点
    """

    def __init__(self):
        # 调用父类的构造函数，并给节点命名为'my_subscriber_node'
        super().__init__('my_subscriber_node')

        # 创建一个订阅者。
        # 参数1: 消息类型 (String)
        # 参数2: 话题名称 ('my_topic') - 必须和发布者的话题名称一致
        # 参数3: 回调函数 (listener_callback) - 收到消息时要执行的函数
        # 参数4: 队列大小 (QoS)
        self.subscription = self.create_subscription(
            String,
            'my_topic',
            self.listener_callback,
            10)
        self.subscription  # 避免未使用变量的警告

    def listener_callback(self, msg):
        # 这个函数在每次接收到消息时被调用
        # msg参数就是接收到的消息对象
        self.get_logger().info(f'I heard: "{msg.data}"')


def main(args=None):
    # 初始化rclpy库
    rclpy.init(args=args)

    # 创建我们的订阅者节点实例
    my_subscriber = MySubscriber()

    # rclpy.spin() 会让节点持续运行，并检查是否有消息到达
    rclpy.spin(my_subscriber)

    # 节点关闭时，销毁节点并关闭rclpy
    my_subscriber.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()